#!/usr/bin/env python3
"""handoff-grava.py — grava um handoff sem depender do agente para carimbo, índice ou commit.

Uso:
  handoff-grava.py --assunto <slug> [--fechado] [--raiz DIR] [--repo DIR ...] [--sem-commit] < corpo.md
  handoff-grava.py --assunto <slug> --indexar handoffs/history/<arquivo>.md [--raiz DIR] [--sem-commit]
  handoff-grava.py --listar [--raiz DIR]
  handoff-grava.py --conferir handoffs/history/<arquivo>.md [--raiz DIR]   (só leitura)

O que faz:
  1. carimbo UTC real (relógio da máquina), nome handoffs/history/<AAAA-MM-DDTHHMMSSZ>-<slug>.md,
     criação exclusiva (sufixo -2, -3... se existir); nunca edita snapshot antigo;
  2. anexa ao snapshot um BLOCO DE ESTADO feito pelo script, não pelo agente: commit (HEAD), e sha256
     dos arquivos citados em crase no corpo e dos arquivos sujos fora de handoffs/ no momento;
  3. latest.md = índice de trabalhos abertos (uma linha por assunto) + ponteiro para o snapshot mais novo;
     --fechado tira o assunto do índice; legado (cópia integral ou ponteiro) é preservado uma vez;
     --repo DIR (repetível) acrescenta ao bloco o commit e os sujos de outro repo onde o trabalho acontece
     (sessão aberta num projeto editando outro); o --conferir passa a conferir esse repo também;
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
PAR_INI = "<!-- handoff-parados:inicio -->"
PAR_FIM = "<!-- handoff-parados:fim -->"
PARADO_DIAS = 3      # sem handoff novo há mais que isso: sai dos abertos (fica em "Parados")
MAX_PARADOS = 50     # teto da lista de parados no latest.md; os snapshots nunca são apagados
TRAVA_SEG = 60


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


REPO_SEC = "### Repo do trabalho: "
MAX_REPOS = 5


def impressao(repo, nomes):
    """Uma impressão (16 hex) de TODOS os arquivos sujos: nome + sha256 de cada, em ordem."""
    h = hashlib.sha256()
    for rel in nomes:
        q = rel_ok(repo, rel)
        h.update(f"{rel}\0{sha_seguro(q) if q is not None and q.is_file() else 'apagado'}\n".encode())
    return h.hexdigest()[:16]


def estado_repo(repo):
    """Linhas do bloco para um repo onde o trabalho acontece fora da raiz do handoff (--repo)."""
    h = git(repo, "rev-parse", "HEAD")
    commit = h.stdout.strip() if h.returncode == 0 else "sem commit"
    br = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    sujos = mudados_git(repo, None if commit == "sem commit" else commit)
    linhas = ["", REPO_SEC + str(repo), f"- commit: {commit} · branch: {br}",
              f"- arquivos sujos: {len(sujos)}" + (" (lista cortada)" if len(sujos) > MAX_SUJOS else ""),
              f"- impressão de todos os sujos: {impressao(repo, sujos)}"]
    for rel in sujos[:MAX_SUJOS]:
        q = rel_ok(repo, rel)
        if q is None:
            continue
        linhas.append(f"- `{rel}` · sha256:{sha_seguro(q) if q.is_file() else 'apagado'} · sujo")
    return linhas


def repos_citados(raiz, corpo):
    """Raízes git de caminhos absolutos citados em crase que não são a raiz do handoff (para avisar)."""
    achados = []
    for c in dict.fromkeys(CITADO.findall(corpo)):
        if not c.startswith(("/", "~/")):
            continue
        p = pathlib.Path(os.path.expanduser(c))
        p = p if p.is_dir() else p.parent
        if not p.is_dir():
            continue
        r = subprocess.run(["git", "-C", str(p), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        top = r.stdout.strip()
        if r.returncode == 0 and top and pathlib.Path(top).resolve() != raiz.resolve() and top not in achados:
            achados.append(top)
    return achados


def bloco_estado(raiz, corpo, repos=()):
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
            + "\n".join(cab + linhas + [ln for r in repos for ln in estado_repo(r)]) + "\n" + EST_FIM + "\n")


def conferir(raiz, rel):
    snap = rel_ok(raiz, rel)
    if snap is None or not snap.is_file():
        erro(f"snapshot inválido: {rel}")
    txt = snap.read_text(encoding="utf-8")
    if EST_INI not in txt or EST_FIM not in txt:
        print("frescor: sem bloco de estado (handoff anterior ao 1.5.2) — não dá para conferir; trate como pista")
        sys.exit(3)
    bloco = txt.split(EST_INI, 1)[1].split(EST_FIM, 1)[0]
    partes = bloco.split("\n" + REPO_SEC)
    bloco = partes[0]
    extras = []
    for sec in partes[1:]:
        caminho, _, resto = sec.partition("\n")
        extras.append((pathlib.Path(caminho.strip()), resto))
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
    for repo, resto in extras:
        problemas += [f"{repo}: {x}" for x in conferir_repo(repo, resto)]
    if info:
        print(info)
    if problemas:
        print("frescor: divergente — o handoff é pista, não fato; confira antes de agir")
        for p in problemas[:40]:
            print(f"  - {p}")
        if len(problemas) > 40:
            print(f"  - … mais {len(problemas) - 40}")
        sys.exit(2)
    rep = "".join(f"; repo do trabalho {r} igual" for r, _ in extras)
    print(f"frescor: igual ({len(arqs)} arquivo(s) conferido(s); commit {commit[:12]}{rep})")


def conferir_repo(repo, sec):
    """Problemas de frescor de um repo do trabalho (seção do bloco gravada com --repo)."""
    if not (repo / ".git").exists() and not eh_git(repo):
        return ["repo do trabalho não existe mais ou não é git"]
    m = re.search(r"^- commit: (\S+)", sec, re.M)
    commit = m[1] if m else "sem commit"
    arqs = {}
    for ln in sec.splitlines():
        a = EST_ARQ.match(ln.strip())
        if a:
            arqs[a["rel"]] = a["h"]
    imp = re.search(r"^- impressão de todos os sujos: ([0-9a-f]+)", sec, re.M)
    agora_sujos = mudados_git(repo, commit) if commit != "sem commit" else mudados_git(repo, None)
    if imp and git(repo, "cat-file", "-e", f"{commit}^{{commit}}").returncode == 0 \
            and impressao(repo, agora_sujos) == imp[1]:
        return []  # todos os arquivos alterados estão iguais ao momento do handoff
    out = []
    for rel, h in arqs.items():
        q = rel_ok(repo, rel)
        agora = sha_seguro(q) if q is not None and q.is_file() else "apagado"
        if agora != h:
            out.append(f"{rel}: " + ("sumiu" if agora == "apagado" else "mudou") + " (sujo no handoff)")
    if commit != "sem commit":
        if git(repo, "cat-file", "-e", f"{commit}^{{commit}}").returncode:
            out.append(f"commit gravado {commit[:12]} não existe mais (rebase/reset?)")
        else:
            fora = [rel for rel in agora_sujos if rel not in arqs]
            if "(lista cortada)" in sec and fora:
                out.append(f"{len(fora)} arquivo(s) fora da lista gravada; a impressão de todos mudou "
                           f"(ex.: {', '.join(fora[:3])})")
            else:
                out += [f"{rel}: mudou depois do handoff (não estava no bloco)" for rel in fora]
    return out


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


def ler_parados(latest):
    try:
        txt = latest.read_text(encoding="utf-8")
    except OSError:
        return {}
    if PAR_INI not in txt or PAR_FIM not in txt:
        return {}
    return entradas_de(txt.split(PAR_INI, 1)[1].split(PAR_FIM, 1)[0])


def separar_parados(raiz, entradas, parados, dias, atual):
    """Abertos sem handoff há mais de `dias` viram parados (menos o assunto desta gravação). Devolve os movidos."""
    if dias <= 0:
        return []
    limite = dt.datetime.now().timestamp() - dias * 86400
    movidos = [s for s, (arq, _) in entradas.items() if s != atual and idade(raiz, arq) < limite]
    for s in movidos:
        parados[s] = entradas.pop(s)
    return movidos


class Trava:
    """flock exclusivo na pasta handoffs/history: vários terminais gravando o índice ao mesmo tempo
    esperam a vez em vez de um apagar a linha do outro. Sem arquivo extra no repo."""

    def __init__(self, pasta):
        self.pasta = pasta
        self.fd = None

    def __enter__(self):
        import fcntl
        self.fd = os.open(self.pasta, os.O_RDONLY)
        fim = dt.datetime.now().timestamp() + TRAVA_SEG
        while True:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if dt.datetime.now().timestamp() > fim:
                    os.close(self.fd)
                    erro(f"índice travado por outra gravação há mais de {TRAVA_SEG}s; tente de novo")
                import time
                time.sleep(0.05)

    def __exit__(self, *_):
        os.close(self.fd)  # fechar solta o flock


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


def montar_latest(raiz, entradas, atual_rel, corpo, parados=None, dias=PARADO_DIAS):
    linhas = [f"- `{s}` · {a} · {q}" for s, (a, q) in ordenar(raiz, entradas)]
    abertos = "\n".join(linhas) if linhas else "- nenhum"
    par = ""
    if parados:
        lp = "\n".join(f"- `{s}` · {a} · {q}" for s, (a, q) in ordenar(raiz, parados))
        par = (f"\n## Parados (sem handoff há mais de {dias} dias)\n\n"
               "Fora dos abertos: o /prime não lista. Gravar um handoff com o mesmo slug volta o assunto "
               f"para os abertos; `--fechado` tira daqui. Snapshots continuam em handoffs/history/.\n\n"
               f"{PAR_INI}\n{lp}\n{PAR_FIM}\n")
    # Só o ponteiro: o corpo fica no snapshot (copiar aqui fazia o latest.md pesar 20 KB a cada leitura).
    tit = titulo_de(corpo) if atual_rel else ""
    rodape = (f"\n---\n\nMais recente: `{atual_rel}`" + (f" — {tit}" if tit else "") + "\n\n"
              "O conteúdo de cada trabalho fica no snapshot citado: abra o do assunto que for continuar "
              "(o /prime faz isso).\n"
              if atual_rel else "\n---\n\nNenhum trabalho aberto.\n")
    return (f"# Handoffs — trabalhos abertos\n\n"
            "Cada linha é um assunto em andamento: leia o snapshot do assunto que for continuar. "
            "Gravado por handoff-grava.py.\n\n"
            f"{INICIO}\n{abertos}\n{FIM}\n{par}{rodape}")


FEC_INI = "<!-- handoff-fechados:inicio -->"
FEC_FIM = "<!-- handoff-fechados:fim -->"
FEC_LINHA = re.compile(r"^- `(?P<slug>[a-z0-9-]+)` · (?P<arq>handoffs/history/[^ ]+\.md) · "
                       r"(?P<quando>\d{2}/\d{2}/\d{4} \d{2}:\d{2}) · (?P<titulo>.*)$")


def titulo_de(texto):
    """Primeiro '# ' do snapshot, sem o prefixo 'Handoff —'; uma linha, até 120 caracteres."""
    for ln in texto.splitlines():
        if ln.startswith("# "):
            t = re.sub(r"^Handoff\s*[—–:-]\s*", "", ln[2:].strip(), flags=re.I)
            return re.sub(r"\s+", " ", t)[:120].replace("`", "'")
    return ""


def ler_fechados(arq):
    """{slug: (arq, 'dd/mm/AAAA HH:MM', titulo)} de handoffs/fechados.md."""
    try:
        txt = arq.read_text(encoding="utf-8")
    except OSError:
        return {}
    if FEC_INI in txt and FEC_FIM in txt:
        txt = txt.split(FEC_INI, 1)[1].split(FEC_FIM, 1)[0]
    out = {}
    for ln in txt.splitlines():
        m = FEC_LINHA.match(ln.strip())
        if m:
            out[m["slug"]] = (m["arq"], m["quando"], m["titulo"])
    return out


def _chave_data(q):
    try:
        return dt.datetime.strptime(q, "%d/%m/%Y %H:%M")
    except ValueError:
        return dt.datetime.min


def gravar_fechados(arq, fechados):
    linhas = [f"- `{s}` · {a} · {q} · {t}" for s, (a, q, t) in
              sorted(fechados.items(), key=lambda kv: _chave_data(kv[1][1]), reverse=True)]
    tmp = arq.with_suffix(".md.tmp")
    tmp.write_text("# Handoffs — trabalhos fechados\n\n"
                   "Um assunto por linha, o fechamento mais recente primeiro: slug · snapshot do fechamento · data · "
                   "título. Para pesquisar trabalho antigo; o /prime não lê. Gravado por handoff-grava.py.\n\n"
                   f"{FEC_INI}\n" + ("\n".join(linhas) if linhas else "- nenhum") + f"\n{FEC_FIM}\n",
                   encoding="utf-8")
    os.replace(tmp, arq)


def recuperar_fechados(raiz, fechados, abertos):
    """Fechados de antes da 1.10.3, pelo log do git (commits 'handoff: <slug> (fechado)'). Devolve os novos."""
    if not eh_git(raiz):
        erro("--recuperar-fechados precisa de repositório git")
    r = git(raiz, "log", "--format=%H%x09%ct%x09%s", "--grep=^handoff: [a-z0-9-]* (fechado)$")
    novos = []
    for ln in r.stdout.splitlines():  # mais recente primeiro
        h, ct, assunto = ln.split("\t", 2)
        m = re.match(r"^handoff: ([a-z0-9-]+) \(fechado\)$", assunto)
        if not m or m[1] in fechados or m[1] in abertos:
            continue
        slug = m[1]
        nomes = git(raiz, "show", "--name-only", "--diff-filter=A", "--format=", h, "--",
                    "handoffs/history").stdout.split()
        arq = next((n for n in nomes if re.search(rf"-{re.escape(slug)}(-\d+)?\.md$", n)), None)
        if not arq:
            continue
        p = rel_ok(raiz, arq)
        tit = titulo_de(p.read_text(encoding="utf-8")) if p is not None and p.is_file() else ""
        fechados[slug] = (arq, dt.datetime.fromtimestamp(int(ct)).strftime("%d/%m/%Y %H:%M"), tit)
        novos.append(slug)
    return novos


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


def arrumar(raiz, hist, latest, arq_fec, a):
    """Sem snapshot novo: recupera fechados do git, move parados e regrava o índice (uma vez por projeto)."""
    if not hist.is_dir():
        erro("projeto sem handoffs/history/")
    sem_symlink(raiz, hist)
    for p in (latest, arq_fec, latest.with_name("indice.txt")):
        if p.exists():
            sem_symlink(raiz, p)
    with Trava(hist):
        entradas, formato = ler_indice(latest)
        if formato != "indice":
            print(f"latest.md sem índice (formato {formato}): nada a arrumar")
            return
        parados = ler_parados(latest)
        fechados = ler_fechados(arq_fec)
        novos = recuperar_fechados(raiz, fechados, set(entradas) | set(parados)) if eh_git(raiz) else []
        movidos = separar_parados(raiz, entradas, parados, a.parado_dias, None)
        par_ord = ordenar(raiz, parados)
        parados = dict(par_ord[:MAX_PARADOS])
        com_copia = "Cópia integral do snapshot mais recente" in latest.read_text(encoding="utf-8")  # antes da 1.11.3
        if not novos and not movidos and len(par_ord) <= MAX_PARADOS and not com_copia:
            print("nada a arrumar: " + f"{len(entradas)} aberto(s), {len(parados)} parado(s), {len(fechados)} fechado(s)")
            return
        gravados = []
        if novos:
            gravar_fechados(arq_fec, fechados)
            gravados.append(arq_fec)
        rodape_rel = ordenar(raiz, entradas)[0][1][0] if entradas else None
        rodape = (raiz / rodape_rel).read_text(encoding="utf-8") if rodape_rel else ""
        tmp = latest.with_suffix(".md.tmp")
        tmp.write_text(montar_latest(raiz, entradas, rodape_rel, rodape, parados, a.parado_dias), encoding="utf-8")
        os.replace(tmp, latest)
        indice = latest.with_name("indice.txt")
        indice.write_text("".join(f"- `{s}` · {x} · {q}\n" for s, (x, q) in ordenar(raiz, entradas)), encoding="utf-8")
        gravados += [latest, indice]
        print(f"arrumado: {len(entradas)} aberto(s), {len(movidos)} movido(s) para parados, "
              f"{len(novos)} fechado(s) recuperado(s)")
        print(commitar(raiz, gravados, "arrumar-indice", False) if not a.sem_commit else "sem commit (--sem-commit)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--assunto", help="slug estável do trabalho (ex.: rea-es); reuse o do índice")
    ap.add_argument("--fechado", action="store_true", help="trabalho terminado: sai do índice")
    ap.add_argument("--indexar", help="registra um snapshot já existente sem criar outro")
    ap.add_argument("--listar", action="store_true", help="mostra o índice e sai")
    ap.add_argument("--conferir", help="compara o bloco de estado de um snapshot com o projeto agora (só leitura)")
    ap.add_argument("--raiz", default=".")
    ap.add_argument("--sem-commit", action="store_true")
    ap.add_argument("--repo", action="append", default=[],
                    help="repositório git onde o trabalho acontece, fora da raiz do handoff (pode repetir)")
    ap.add_argument("--fechados", action="store_true", help="lista os trabalhos fechados (handoffs/fechados.md) e sai")
    ap.add_argument("--recuperar-fechados", action="store_true",
                    help="preenche handoffs/fechados.md com os fechados antigos, pelo log do git")
    ap.add_argument("--arrumar", action="store_true",
                    help="sem snapshot novo: recupera fechados, move parados e regrava o índice (commit só desses)")
    ap.add_argument("--parado-dias", type=int, default=int(os.environ.get("HANDOFF_PARADO_DIAS", PARADO_DIAS)),
                    help=f"assunto sem handoff há mais que isso sai dos abertos (padrão {PARADO_DIAS}; 0 desliga)")
    a = ap.parse_args()

    raiz = pathlib.Path(a.raiz).absolute()
    if raiz == pathlib.Path.home():
        erro("a home não é raiz de projeto")
    hist = raiz / "handoffs" / "history"
    latest = raiz / "handoffs" / "latest.md"
    if a.conferir:
        conferir(raiz, a.conferir)
        return
    if a.listar:
        entradas, formato = ler_indice(latest)
        for s, (arq, q) in ordenar(raiz, entradas):
            print(f"{s}\t{arq}\t{q}")
        for s, (arq, q) in ordenar(raiz, ler_parados(latest)):
            print(f"{s}\t{arq}\t{q}\tparado")
        if formato != "indice":
            print(f"(latest.md sem índice: formato {formato})", file=sys.stderr)
        return

    arq_fec = raiz / "handoffs" / "fechados.md"
    if a.fechados:
        for s, (arq, q, t) in sorted(ler_fechados(arq_fec).items(), key=lambda kv: _chave_data(kv[1][1]),
                                     reverse=True):
            print(f"{s}\t{arq}\t{q}\t{t}")
        return

    if a.recuperar_fechados:
        hist.mkdir(parents=True, exist_ok=True)
        sem_symlink(raiz, hist)
        if arq_fec.exists():
            sem_symlink(raiz, arq_fec)
        with Trava(hist):
            fechados = ler_fechados(arq_fec)
            abertos = set(ler_indice(latest)[0]) | set(ler_parados(latest))
            novos = recuperar_fechados(raiz, fechados, abertos)
            if novos:
                gravar_fechados(arq_fec, fechados)
            print(f"{len(novos)} fechado(s) recuperado(s)" + (": " + ", ".join(novos) if novos else ""))
            if novos and not a.sem_commit:
                print(commitar(raiz, [arq_fec], "fechados-recuperados", False))
        return

    if a.arrumar:
        arrumar(raiz, hist, latest, arq_fec, a)
        return

    if not a.assunto or not SLUG.match(a.assunto):
        erro("--assunto obrigatório: minúsculas, números e hífen (ex.: rea-es)")
    hist.mkdir(parents=True, exist_ok=True)
    sem_symlink(raiz, hist)
    if latest.exists():
        sem_symlink(raiz, latest)
    if arq_fec.exists():
        sem_symlink(raiz, arq_fec)

    # Parte lenta (hash dos arquivos) fora da trava; índice, gravação e commit dentro dela.
    avisos, corpo = [], None
    if not a.indexar:
        corpo = sys.stdin.read()
        if len(corpo.strip()) < 200:
            erro("corpo do handoff vazio ou curto demais (stdin)")
        if EST_INI in corpo:  # bloco escrito à mão ou copiado de outro handoff não vale: sai
            antes, resto = corpo.split(EST_INI, 1)
            corpo = antes + (resto.split(EST_FIM, 1)[1] if EST_FIM in resto else "")
        repos = []
        for r in a.repo[:MAX_REPOS]:
            rp = pathlib.Path(os.path.expanduser(r)).absolute()
            top = git(rp, "rev-parse", "--show-toplevel").stdout.strip() if rp.is_dir() else ""
            if not top or pathlib.Path(top).resolve() == pathlib.Path.home().resolve():
                erro(f"--repo precisa ser um repositório git: {r}")
            if pathlib.Path(top).resolve() != raiz.resolve() and pathlib.Path(top) not in repos:
                repos.append(pathlib.Path(top))
        soltos = [c for c in repos_citados(raiz, corpo) if pathlib.Path(c) not in repos]
        if soltos:
            avisos.append("aviso: o handoff cita outro(s) repo(s) sem --repo: " + ", ".join(soltos)
                          + ". Se o trabalho acontece lá, grave de novo com --repo <caminho> para o --conferir cobrir.")
        if not any(s in corpo for s in ("## Perguntas-teste", "## Test questions", "## Preguntas de control")):
            avisos.append("aviso: handoff sem a seção Perguntas-teste — o prime não vai dar a nota N/5; "
                          "grave de novo com as 5 perguntas do modelo.")
        if not any(s in corpo for s in ("## Não fazer", "## Do not do", "## No hacer")):
            avisos.append("aviso: falta a seção Não fazer (restrições e travas) — o prime não terá a lista do que "
                          "não pode mudar; grave de novo com todas as restrições, uma por item.")
        corpo = corpo.rstrip() + "\n" + bloco_estado(raiz, corpo, repos)

    with Trava(hist):
        entradas, formato = ler_indice(latest)
        parados = ler_parados(latest)
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
        else:
            carimbo = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
            snap = criar_exclusivo(hist, f"{carimbo}-{a.assunto}", corpo)
            gravados.append(snap)

        rel = str(snap.relative_to(raiz))
        parados.pop(a.assunto, None)
        fechados = ler_fechados(arq_fec)
        antes_fec = dict(fechados)
        if a.fechado:
            entradas.pop(a.assunto, None)
            fechados[a.assunto] = (rel, dt.datetime.fromtimestamp(snap.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
                                   titulo_de(snap.read_text(encoding="utf-8")))
        else:
            entradas[a.assunto] = (rel, quando_de(snap))
            fechados.pop(a.assunto, None)  # reaberto
        if fechados != antes_fec:
            gravar_fechados(arq_fec, fechados)
            gravados.append(arq_fec)
        movidos = separar_parados(raiz, entradas, parados, a.parado_dias, a.assunto)
        par_ord = ordenar(raiz, parados)
        cortados = len(par_ord) - MAX_PARADOS
        parados = dict(par_ord[:MAX_PARADOS])

        # O rodapé mostra o snapshot mais novo entre os abertos (ou este, se acabou de ser gravado).
        if entradas:
            mais_novo = ordenar(raiz, entradas)[0][1][0]
            rodape_rel = rel if (not a.fechado and not a.indexar) else mais_novo
            rodape = (raiz / rodape_rel).read_text(encoding="utf-8")
        else:
            rodape_rel, rodape = None, ""
        novo = montar_latest(raiz, entradas, rodape_rel, rodape, parados, a.parado_dias)
        tmp = latest.with_suffix(".md.tmp")
        tmp.write_text(novo, encoding="utf-8")
        os.replace(tmp, latest)
        indice = latest.with_name("indice.txt")
        if indice.exists():
            sem_symlink(raiz, indice)
        indice.write_text("".join(f"- `{s}` · {a2} · {q}\n" for s, (a2, q) in ordenar(raiz, entradas)),
                          encoding="utf-8")

        # leitura de volta
        lido, fmt = ler_indice(latest)
        if fmt != "indice" or (not a.fechado and lido.get(a.assunto, ("",))[0] != rel):
            erro("leitura de volta do latest.md não bate")
        gravados += [latest, indice]
        resultado_commit = commitar(raiz, gravados, a.assunto, a.fechado) if not a.sem_commit \
            else "sem commit (--sem-commit)"

    print(f"snapshot: {rel}")
    if legado:
        print(f"legado preservado: {legado.relative_to(raiz)}")
    print(f"latest.md: {len(lido)} assunto(s) aberto(s): {', '.join(sorted(lido)) or 'nenhum'}")
    if movidos:
        print(f"{len(movidos)} assunto(s) sem handoff há mais de {a.parado_dias} dias movido(s) para os parados: "
              + ", ".join(sorted(movidos)))
    if cortados > 0:
        print(f"{cortados} parado(s) mais antigo(s) saíram da lista (snapshots seguem em handoffs/history/)")
    print(resultado_commit)
    for av in avisos:
        print(av)
    if not a.fechado and not a.indexar:
        # Caminho exato deste snapshot: outra sessão pode gravar um handoff mais novo no mesmo projeto.
        print("retomar ESTE handoff numa sessão nova (Codex: /new no lugar de /clear):")
        print("  /clear")
        print(f"  /prime {rel}")


if __name__ == "__main__":
    main()
