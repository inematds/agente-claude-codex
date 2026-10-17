#!/usr/bin/env python3
"""handoff-grava.py — grava um handoff sem depender do agente para carimbo, índice ou commit.

Uso:
  handoff-grava.py --assunto <slug> [--fechado] [--raiz DIR] [--sem-commit] < corpo.md
  handoff-grava.py --assunto <slug> --indexar handoffs/history/<arquivo>.md [--raiz DIR] [--sem-commit]
  handoff-grava.py --listar [--raiz DIR]
  handoff-grava.py --conferir handoffs/history/<arquivo>.md [--raiz DIR]   (só leitura)

O que faz:
  1. carimbo UTC real (relógio da máquina), nome handoffs/history/<AAAA-MM-DDTHHMMSSZ>-<slug>.md,
     criação exclusiva (sufixo -2, -3... se existir); nunca edita snapshot antigo;
  2. anexa ao snapshot um BLOCO DE ESTADO feito pelo script, não pelo agente: commit (HEAD), e sha256
     dos arquivos citados em crase no corpo e dos arquivos sujos fora de handoffs/ no momento;
  3. latest.md = índice de trabalhos abertos (uma linha por assunto) + cópia integral do snapshot novo;
     --fechado tira o assunto do índice; legado (cópia integral ou ponteiro) é preservado uma vez;
  4. se a raiz for repositório git, commita SÓ o snapshot e o latest.md (pathspec); nunca faz push.

--conferir compara o bloco de estado com o projeto agora (frescor do handoff):
  saída 0 = igual (só handoffs/ mudou), 2 = divergente (lista o que mudou), 3 = snapshot sem bloco.
  Divergente quer dizer: o handoff é pista, não fato — confira antes de agir.
"""
import argparse
import datetime as dt
import hashlib
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
EST_INI = "<!-- handoff-estado:inicio -->"
EST_FIM = "<!-- handoff-estado:fim -->"
CITADO = re.compile(r"`([^`\s]+)`")
EST_ARQ = re.compile(r"^- `(?P<rel>[^`]+)` · sha256:(?P<h>[0-9a-f]+|apagado|ilegivel) · (?P<tipo>citado|sujo)")
MAX_CITADOS = 20
MAX_SUJOS = 200


GRANDE = 100 * 1024 * 1024


def sha(p):
    """sha256 (12 hex) lido em blocos; acima de 100 MB, tamanho + 1 MB do começo + 1 MB do fim."""
    h = hashlib.sha256()
    tam = p.stat().st_size
    with open(p, "rb") as fh:
        if tam > GRANDE:
            h.update(str(tam).encode())
            h.update(fh.read(1 << 20))
            fh.seek(-(1 << 20), os.SEEK_END)
            h.update(fh.read())
        else:
            for bloco in iter(lambda: fh.read(1 << 20), b""):
                h.update(bloco)
    return h.hexdigest()[:12]


def sha_seguro(p):
    """sha() que não derruba a gravação: arquivo ilegível vira 'ilegivel'."""
    try:
        return sha(p)
    except OSError:
        return "ilegivel"


def rel_ok(raiz, rel):
    """Caminho relativo seguro dentro da raiz (sem absoluto, ~, .., URL ou symlink no caminho)."""
    if rel.startswith(("/", "~")) or "://" in rel or ".." in pathlib.PurePosixPath(rel).parts:
        return None
    p = raiz / rel
    atual = p
    while atual != raiz and atual.parent != atual:
        if atual.is_symlink():
            return None
        atual = atual.parent
    try:
        p.resolve().relative_to(raiz.resolve())
    except ValueError:
        return None
    return p


def eh_git(raiz):
    return git(raiz, "rev-parse", "--is-inside-work-tree").stdout.strip() == "true"


def mudados_git(raiz, base):
    """Arquivos (fora de handoffs/) que diferem de `base` (commit ou HEAD) agora, + não rastreados."""
    ref = base or "HEAD"
    nomes = set()
    r = git(raiz, "diff", "--name-only", ref, "--", ".", ":(exclude)handoffs")
    nomes |= {ln for ln in r.stdout.splitlines() if ln}
    r = git(raiz, "ls-files", "--others", "--exclude-standard", "--", ".", ":(exclude)handoffs")
    nomes |= {ln for ln in r.stdout.splitlines() if ln}
    return sorted(nomes)


def bloco_estado(raiz, corpo):
    linhas, vistos = [], set()
    commit = "sem git"
    if eh_git(raiz):
        h = git(raiz, "rev-parse", "HEAD")
        commit = h.stdout.strip() if h.returncode == 0 else "sem commit"
        br = git(raiz, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        sujos = mudados_git(raiz, None if commit == "sem commit" else commit)
        for rel in sujos[:MAX_SUJOS]:
            p = rel_ok(raiz, rel)
            if p is None:
                continue
            h12 = sha_seguro(p) if p.is_file() else "apagado"
            linhas.append(f"- `{rel}` · sha256:{h12} · sujo")
            vistos.add(rel)
        cab = [f"- commit: {commit} · branch: {br}",
               f"- arquivos sujos fora de handoffs/: {len(sujos)}" + (" (lista cortada)" if len(sujos) > MAX_SUJOS else "")]
    else:
        cab = [f"- commit: {commit}"]
    n = 0
    for rel in dict.fromkeys(CITADO.findall(corpo)):
        if n >= MAX_CITADOS or rel in vistos:
            continue
        p = rel_ok(raiz, rel)
        if p is None or not p.is_file():
            continue
        linhas.append(f"- `{rel}` · sha256:{sha_seguro(p)} · citado")
        vistos.add(rel)
        n += 1
    return ("\n\n" + EST_INI + "\n## Estado gravado pelo script (não editar)\n\n"
            "Gravado por handoff-grava.py no momento do handoff. `--conferir` compara com o projeto agora.\n\n"
            + "\n".join(cab + linhas) + "\n" + EST_FIM + "\n")


def conferir(raiz, rel):
    snap = rel_ok(raiz, rel)
    if snap is None or not snap.is_file():
        erro(f"snapshot inválido: {rel}")
    txt = snap.read_text(encoding="utf-8")
    if EST_INI not in txt or EST_FIM not in txt:
        print("frescor: sem bloco de estado (handoff anterior ao 1.5.2) — não dá para conferir; trate como pista")
        sys.exit(3)
    bloco = txt.split(EST_INI, 1)[1].split(EST_FIM, 1)[0]
    m = re.search(r"^- commit: (\S+)", bloco, re.M)
    commit = m[1] if m else "sem git"
    arqs = {}
    for ln in bloco.splitlines():
        a = EST_ARQ.match(ln.strip())
        if a:
            arqs[a["rel"]] = (a["h"], a["tipo"])
    problemas, info = [], ""

    def atual(rel):
        p = rel_ok(raiz, rel)
        return sha_seguro(p) if p is not None and p.is_file() else "apagado"

    for rel, (h, tipo) in arqs.items():
        agora = atual(rel)
        if agora != h:
            problemas.append(f"{rel}: " + ("sumiu" if agora == "apagado" else "mudou") + f" ({tipo} no handoff)")
    if commit not in ("sem git", "sem commit") and eh_git(raiz):
        if git(raiz, "cat-file", "-e", f"{commit}^{{commit}}").returncode:
            problemas.append(f"commit gravado {commit[:12]} não existe mais (rebase/reset?)")
        else:
            n = git(raiz, "rev-list", "--count", f"{commit}..HEAD", "--", ".", ":(exclude)handoffs").stdout.strip()
            if n and n != "0":
                info = f"{n} commit(s) depois do handoff fora de handoffs/ (só conta se o conteúdo mudou)"
            for rel in mudados_git(raiz, commit):
                if rel in arqs:
                    continue  # já conferido pelo hash
                problemas.append(f"{rel}: mudou depois do handoff (não estava no bloco)")
    if info:
        print(info)
    if problemas:
        print("frescor: divergente — o handoff é pista, não fato; confira antes de agir")
        for p in problemas[:40]:
            print(f"  - {p}")
        if len(problemas) > 40:
            print(f"  - … mais {len(problemas) - 40}")
        sys.exit(2)
    print(f"frescor: igual ({len(arqs)} arquivo(s) conferido(s); commit {commit[:12]})")


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
    ap.add_argument("--conferir", help="compara o bloco de estado de um snapshot com o projeto agora (só leitura)")
    ap.add_argument("--raiz", default=".")
    ap.add_argument("--sem-commit", action="store_true")
    a = ap.parse_args()

    raiz = pathlib.Path(a.raiz).absolute()
    if raiz == pathlib.Path.home():
        erro("a home não é raiz de projeto")
    hist = raiz / "handoffs" / "history"
    latest = raiz / "handoffs" / "latest.md"
    if a.conferir:
        conferir(raiz, a.conferir)
        return
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
        if EST_INI in corpo:  # bloco escrito à mão ou copiado de outro handoff não vale: sai
            antes, resto = corpo.split(EST_INI, 1)
            corpo = antes + (resto.split(EST_FIM, 1)[1] if EST_FIM in resto else "")
        corpo = corpo.rstrip() + "\n" + bloco_estado(raiz, corpo)
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
