#!/usr/bin/env python3
"""handoff-grava.py — grava um handoff sem depender do agente para carimbo, índice ou commit.

Uso:
  handoff-grava.py --assunto <slug> [--fechado] [--raiz DIR] [--sem-commit] < corpo.md
  handoff-grava.py --assunto <slug> --indexar handoffs/history/<arquivo>.md [--raiz DIR] [--sem-commit]
  handoff-grava.py --listar [--raiz DIR]

O que faz:
  1. carimbo UTC real (relógio da máquina), nome handoffs/history/<AAAA-MM-DDTHHMMSSZ>-<slug>.md,
     criação exclusiva (sufixo -2, -3... se existir); nunca edita snapshot antigo;
  2. latest.md = índice de trabalhos abertos (uma linha por assunto) + cópia integral do snapshot novo;
     --fechado tira o assunto do índice; legado (cópia integral ou ponteiro) é preservado uma vez;
  3. se a raiz for repositório git, commita SÓ o snapshot e o latest.md (pathspec); nunca faz push.
"""
import argparse
import datetime as dt
import os
import pathlib
import re
import subprocess
import sys

INICIO = "<!-- handoff-indice:inicio -->"
FIM = "<!-- handoff-indice:fim -->"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")
LINHA = re.compile(r"^- `(?P<slug>[a-z0-9-]+)` · (?P<arq>handoffs/history/[^ ]+\.md) · (?P<quando>.+)$")
NOME = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{6}Z)")


def erro(msg):
    print(f"handoff-grava: {msg}", file=sys.stderr)
    sys.exit(1)


def sem_symlink(raiz, p):
    """Recusa symlink em qualquer ponto entre a raiz e p, e caminho que sai da raiz."""
    atual = p
    while True:
        if atual.is_symlink():
            erro(f"symlink recusado: {atual}")
        if atual == raiz or atual.parent == atual:
            break
        atual = atual.parent
    try:
        p.resolve().relative_to(raiz.resolve())
    except ValueError:
        erro(f"fora da raiz: {p}")


def entradas_de(texto):
    ent = {}
    for ln in texto.splitlines():
        m = LINHA.match(ln.strip())
        if m:
            ent[m["slug"]] = (m["arq"], m["quando"])
    return ent


def ler_indice(latest):
    """(entradas {slug: (arq, quando)}, formato) do latest.md atual. Se uma sessão com a skill antiga
    sobrescreveu o latest.md, o índice volta do handoffs/indice.txt (cópia gravada ao lado)."""
    copia = latest.with_name("indice.txt")
    reserva = entradas_de(copia.read_text(encoding="utf-8")) if copia.is_file() else {}
    if not latest.exists():
        return reserva, "nenhum"
    txt = latest.read_text(encoding="utf-8")
    if INICIO in txt and FIM in txt:
        return entradas_de(txt.split(INICIO, 1)[1].split(FIM, 1)[0]), "indice"
    linhas = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    if len(linhas) == 1 and linhas[0].startswith("handoffs/history/") and linhas[0].endswith(".md"):
        return reserva, "ponteiro"
    return reserva, "copia"


def preservar_legado(raiz, latest, formato):
    """Cópia integral que não existe em history/ vira <mtime>-anterior.md (uma vez)."""
    if formato != "copia":
        return None
    txt = latest.read_text(encoding="utf-8")
    hist = raiz / "handoffs" / "history"
    for f in hist.glob("*.md"):
        try:
            if f.read_text(encoding="utf-8") == txt:
                return None
        except OSError:
            continue
    carimbo = dt.datetime.fromtimestamp(latest.stat().st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    return criar_exclusivo(hist, f"{carimbo}-anterior", txt)


def criar_exclusivo(pasta, base, conteudo):
    for n in range(1, 100):
        nome = f"{base}.md" if n == 1 else f"{base}-{n}.md"
        p = pasta / nome
        try:
            with open(p, "x", encoding="utf-8") as fh:
                fh.write(conteudo)
            return p
        except FileExistsError:
            continue
    erro(f"não achei nome livre para {base}")


def quando_de(p):
    return dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m %H:%M")


def idade(raiz, rel):
    try:
        return (raiz / rel).stat().st_mtime
    except OSError:
        return 0.0


def ordenar(raiz, entradas):
    """Mais recente primeiro, pela hora em que o arquivo foi gravado (o nome pode mentir)."""
    return sorted(entradas.items(), key=lambda kv: idade(raiz, kv[1][0]), reverse=True)


def montar_latest(raiz, entradas, atual_rel, corpo):
    linhas = [f"- `{s}` · {a} · {q}" for s, (a, q) in ordenar(raiz, entradas)]
    abertos = "\n".join(linhas) if linhas else "- nenhum"
    rodape = (f"\n---\n\nCópia integral do snapshot mais recente ({atual_rel}):\n\n{corpo}"
              if atual_rel else "\n---\n\nNenhum trabalho aberto.\n")
    return (f"# Handoffs — trabalhos abertos\n\n"
            "Cada linha é um assunto em andamento: leia o snapshot do assunto que for continuar. "
            "Gravado por handoff-grava.py.\n\n"
            f"{INICIO}\n{abertos}\n{FIM}\n{rodape}")


def git(raiz, *args):
    return subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True)


def commitar(raiz, caminhos, slug, fechado):
    if git(raiz, "rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        return "não é repositório git: sem commit"
    rels = [str(p.relative_to(raiz)) for p in caminhos]
    r = git(raiz, "add", "--", *rels)
    if r.returncode:
        return f"git add falhou: {r.stderr.strip()}"
    if not git(raiz, "diff", "--cached", "--quiet", "--", *rels).returncode:
        return "nada novo para commitar"
    msg = f"handoff: {slug}" + (" (fechado)" if fechado else "")
    r = git(raiz, "commit", "-q", "-m", msg, "--", *rels)
    if r.returncode:
        return f"git commit falhou: {r.stderr.strip() or r.stdout.strip()}"
    autor = git(raiz, "log", "-1", "--format=%h %an <%ae>").stdout.strip()
    return f"commit {autor} (sem push)"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--assunto", help="slug estável do trabalho (ex.: rea-es); reuse o do índice")
    ap.add_argument("--fechado", action="store_true", help="trabalho terminado: sai do índice")
    ap.add_argument("--indexar", help="registra um snapshot já existente sem criar outro")
    ap.add_argument("--listar", action="store_true", help="mostra o índice e sai")
    ap.add_argument("--raiz", default=".")
    ap.add_argument("--sem-commit", action="store_true")
    a = ap.parse_args()

    raiz = pathlib.Path(a.raiz).absolute()
    if raiz == pathlib.Path.home():
        erro("a home não é raiz de projeto")
    hist = raiz / "handoffs" / "history"
    latest = raiz / "handoffs" / "latest.md"
    entradas, formato = ler_indice(latest)

    if a.listar:
        for s, (arq, q) in ordenar(raiz, entradas):
            print(f"{s}\t{arq}\t{q}")
        if formato != "indice":
            print(f"(latest.md sem índice: formato {formato})", file=sys.stderr)
        return

    if not a.assunto or not SLUG.match(a.assunto):
        erro("--assunto obrigatório: minúsculas, números e hífen (ex.: rea-es)")
    hist.mkdir(parents=True, exist_ok=True)
    sem_symlink(raiz, hist)
    if latest.exists():
        sem_symlink(raiz, latest)

    gravados = []
    legado = preservar_legado(raiz, latest, formato)
    if legado:
        gravados.append(legado)
        entradas.setdefault("anterior", (str(legado.relative_to(raiz)), quando_de(legado)))

    if a.indexar:
        snap = (raiz / a.indexar)
        sem_symlink(raiz, snap)
        if not snap.is_file() or snap.parent.resolve() != hist.resolve():
            erro(f"--indexar precisa de um arquivo em handoffs/history/: {a.indexar}")
        corpo = snap.read_text(encoding="utf-8")
    else:
        corpo = sys.stdin.read()
        if len(corpo.strip()) < 200:
            erro("corpo do handoff vazio ou curto demais (stdin)")
        carimbo = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        snap = criar_exclusivo(hist, f"{carimbo}-{a.assunto}", corpo)
        gravados.append(snap)

    rel = str(snap.relative_to(raiz))
    if a.fechado:
        entradas.pop(a.assunto, None)
    else:
        entradas[a.assunto] = (rel, quando_de(snap))

    # O rodapé mostra o snapshot mais novo entre os abertos (ou este, se acabou de ser gravado).
    if entradas:
        mais_novo = ordenar(raiz, entradas)[0][1][0]
        rodape_rel = rel if (not a.fechado and not a.indexar) else mais_novo
        rodape = (raiz / rodape_rel).read_text(encoding="utf-8")
    else:
        rodape_rel, rodape = None, ""
    novo = montar_latest(raiz, entradas, rodape_rel, rodape)
    tmp = latest.with_suffix(".md.tmp")
    tmp.write_text(novo, encoding="utf-8")
    os.replace(tmp, latest)
    indice = latest.with_name("indice.txt")
    if indice.exists():
        sem_symlink(raiz, indice)
    indice.write_text("".join(f"- `{s}` · {a} · {q}\n" for s, (a, q) in ordenar(raiz, entradas)), encoding="utf-8")

    # leitura de volta
    lido, fmt = ler_indice(latest)
    if fmt != "indice" or (not a.fechado and lido.get(a.assunto, ("",))[0] != rel):
        erro("leitura de volta do latest.md não bate")
    gravados += [latest, indice]

    print(f"snapshot: {rel}")
    if legado:
        print(f"legado preservado: {legado.relative_to(raiz)}")
    print(f"latest.md: {len(lido)} assunto(s) aberto(s): {', '.join(sorted(lido)) or 'nenhum'}")
    print(commitar(raiz, gravados, a.assunto, a.fechado) if not a.sem_commit else "sem commit (--sem-commit)")


if __name__ == "__main__":
    main()
