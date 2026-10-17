"""Testes do skills/session-handoff/scripts/handoff-grava.py (pytest)."""
import os
import pathlib
import re
import subprocess
import sys
import time

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "skills/session-handoff/scripts/handoff-grava.py"
CORPO = "# Handoff — teste\n\n" + "linha de estado do trabalho\n" * 20


def rodar(raiz, *args, corpo=CORPO, ok=True):
    r = subprocess.run([sys.executable, str(SCRIPT), "--raiz", str(raiz), *args],
                       input=corpo, capture_output=True, text=True)
    if ok:
        assert r.returncode == 0, r.stderr
    return r


def git(raiz, *args):
    return subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True, check=True).stdout


def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@t")
    git(tmp_path, "config", "user.name", "teste")
    (tmp_path / "CLAUDE.md").write_text("x")
    git(tmp_path, "add", "CLAUDE.md")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def indice(raiz):
    r = rodar(raiz, "--listar")
    return [ln.split("\t")[0] for ln in r.stdout.splitlines() if ln]


def test_carimbo_real_e_nome_com_slug(tmp_path):
    antes = time.time()
    r = rodar(tmp_path, "--assunto", "rea-es", "--sem-commit")
    nome = re.search(r"snapshot: handoffs/history/(\S+)", r.stdout)[1]
    m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{6}Z)-rea-es\.md$", nome)
    assert m
    t = time.mktime(time.strptime(m[1], "%Y-%m-%dT%H%M%SZ")) - time.timezone
    assert abs(t - antes) < 5


def test_dois_assuntos_convivem_no_indice(tmp_path):
    rodar(tmp_path, "--assunto", "rea-es", "--sem-commit")
    rodar(tmp_path, "--assunto", "cerebro", "--sem-commit")
    rodar(tmp_path, "--assunto", "rea-es", "--sem-commit")
    assert indice(tmp_path) == ["rea-es", "cerebro"]
    assert len(list((tmp_path / "handoffs/history").glob("*.md"))) == 3


def test_latest_tem_copia_integral_do_mais_novo(tmp_path):
    rodar(tmp_path, "--assunto", "a", "--sem-commit")
    rodar(tmp_path, "--assunto", "b", "--sem-commit", corpo=CORPO + "MARCA-B\n")
    assert "MARCA-B" in (tmp_path / "handoffs/latest.md").read_text()


def test_fechado_sai_do_indice(tmp_path):
    rodar(tmp_path, "--assunto", "a", "--sem-commit")
    rodar(tmp_path, "--assunto", "b", "--sem-commit")
    rodar(tmp_path, "--assunto", "a", "--fechado", "--sem-commit")
    assert indice(tmp_path) == ["b"]


def test_mesmo_segundo_nao_sobrescreve(tmp_path):
    for _ in range(3):
        rodar(tmp_path, "--assunto", "a", "--sem-commit")
    assert len(list((tmp_path / "handoffs/history").glob("*.md"))) == 3


def test_legado_copia_integral_preservado(tmp_path):
    (tmp_path / "handoffs/history").mkdir(parents=True)
    (tmp_path / "handoffs/latest.md").write_text(CORPO + "LEGADO\n")
    r = rodar(tmp_path, "--assunto", "a", "--sem-commit")
    assert "legado preservado" in r.stdout
    leg = list((tmp_path / "handoffs/history").glob("*-anterior.md"))
    assert len(leg) == 1 and "LEGADO" in leg[0].read_text()
    assert set(indice(tmp_path)) == {"a", "anterior"}


def test_indexar_existente_sem_criar(tmp_path):
    h = tmp_path / "handoffs/history"
    h.mkdir(parents=True)
    (h / "2026-10-15T120000Z-cerebro.md").write_text(CORPO)
    rodar(tmp_path, "--assunto", "cerebro", "--indexar", "handoffs/history/2026-10-15T120000Z-cerebro.md",
          "--sem-commit")
    assert indice(tmp_path) == ["cerebro"]
    assert len(list(h.glob("*.md"))) == 1


def test_recusa_slug_ruim_e_corpo_vazio(tmp_path):
    assert rodar(tmp_path, "--assunto", "Rea ES", ok=False).returncode
    assert rodar(tmp_path, "--assunto", "a", corpo="", ok=False).returncode


def test_recusa_symlink(tmp_path):
    fora = tmp_path / "fora"
    fora.mkdir()
    proj = tmp_path / "p"
    (proj / "handoffs").mkdir(parents=True)
    os.symlink(fora, proj / "handoffs/history")
    assert rodar(proj, "--assunto", "a", "--sem-commit", ok=False).returncode
    assert not list(fora.iterdir())


def test_commit_so_dos_arquivos_do_handoff(tmp_path):
    raiz = repo(tmp_path)
    (raiz / "alheio.txt").write_text("staged por outra pessoa")
    git(raiz, "add", "alheio.txt")
    (raiz / "sujo.txt").write_text("não rastreado")
    r = rodar(raiz, "--assunto", "rea-es")
    assert "commit" in r.stdout and "sem push" in r.stdout
    arquivos = git(raiz, "show", "--name-only", "--format=", "HEAD").split()
    assert sorted(arquivos)[0] == "handoffs/history/" + sorted(arquivos)[0].split("/")[-1]
    assert set(a.split("/")[0] for a in arquivos) == {"handoffs"} and "handoffs/latest.md" in arquivos
    assert git(raiz, "log", "-1", "--format=%s") == "handoff: rea-es\n"
    assert "A  alheio.txt" in git(raiz, "status", "--short")  # continua staged, fora do commit


def test_fora_de_repo_nao_commita(tmp_path):
    r = rodar(tmp_path, "--assunto", "a")
    assert "não é repositório git" in r.stdout


def test_indice_sobrevive_a_latest_sobrescrito_pela_skill_antiga(tmp_path):
    rodar(tmp_path, "--assunto", "a", "--sem-commit")
    rodar(tmp_path, "--assunto", "b", "--sem-commit")
    snap = sorted((tmp_path / "handoffs/history").glob("*-b.md"))[0]
    (tmp_path / "handoffs/latest.md").write_text(snap.read_text())  # sessão antiga copia o dela
    rodar(tmp_path, "--assunto", "c", "--sem-commit")
    assert set(indice(tmp_path)) == {"a", "b", "c"}
    assert not list((tmp_path / "handoffs/history").glob("*-anterior.md"))


def test_commit_leva_indice_txt(tmp_path):
    raiz = repo(tmp_path)
    rodar(raiz, "--assunto", "a")
    assert "handoffs/indice.txt" in git(raiz, "show", "--name-only", "--format=", "HEAD").split()


# --- 1.5.2: bloco de estado gravado pelo script + --conferir (frescor do handoff) ---

def snap_de(r):
    return re.search(r"snapshot: (\S+)", r.stdout)[1]


def conferir(raiz, snap):
    return subprocess.run([sys.executable, str(SCRIPT), "--raiz", str(raiz), "--conferir", snap],
                          capture_output=True, text=True)


def com_citacao(*rels):
    return CORPO + "".join(f"- `{r}` — arquivo do trabalho\n" for r in rels)


def test_bloco_de_estado_tem_head_e_hash_do_citado(tmp_path):
    raiz = repo(tmp_path)
    (raiz / "app.py").write_text("v1\n")
    git(raiz, "add", "app.py"); git(raiz, "commit", "-qm", "app")
    head = git(raiz, "rev-parse", "HEAD").strip()
    r = rodar(raiz, "--assunto", "a", corpo=com_citacao("app.py", "/etc/passwd", "../fora.txt", "nao-existe.md"))
    txt = (raiz / snap_de(r)).read_text()
    assert "<!-- handoff-estado:inicio -->" in txt and f"commit: {head}" in txt
    import hashlib
    h = hashlib.sha256(b"v1\n").hexdigest()[:12]
    assert f"`app.py` · sha256:{h} · citado" in txt
    assert "passwd" not in txt.split("handoff-estado:inicio")[1]
    assert "fora.txt" not in txt.split("handoff-estado:inicio")[1]


def test_conferir_igual_mesmo_depois_do_commit_do_handoff(tmp_path):
    raiz = repo(tmp_path)
    (raiz / "app.py").write_text("v1\n")
    git(raiz, "add", "app.py"); git(raiz, "commit", "-qm", "app")
    r = rodar(raiz, "--assunto", "a", corpo=com_citacao("app.py"))
    c = conferir(raiz, snap_de(r))
    assert c.returncode == 0, c.stdout + c.stderr
    assert "frescor: igual" in c.stdout


def test_conferir_acusa_arquivo_citado_que_mudou(tmp_path):
    raiz = repo(tmp_path)
    (raiz / "app.py").write_text("v1\n")
    git(raiz, "add", "app.py"); git(raiz, "commit", "-qm", "app")
    r = rodar(raiz, "--assunto", "a", corpo=com_citacao("app.py"))
    (raiz / "app.py").write_text("v2\n")
    c = conferir(raiz, snap_de(r))
    assert c.returncode == 2
    assert "app.py" in c.stdout and "mudou" in c.stdout


def test_conferir_acusa_commit_novo_em_arquivo_nao_citado(tmp_path):
    raiz = repo(tmp_path)
    r = rodar(raiz, "--assunto", "a")
    (raiz / "outro.py").write_text("x\n")
    git(raiz, "add", "outro.py"); git(raiz, "commit", "-qm", "outro")
    c = conferir(raiz, snap_de(r))
    assert c.returncode == 2
    assert "outro.py" in c.stdout and "1 commit" in c.stdout


def test_trabalho_sujo_commitado_depois_nao_e_divergencia(tmp_path):
    raiz = repo(tmp_path)
    (raiz / "wip.py").write_text("meio\n")          # sujo (não rastreado) ao gravar
    r = rodar(raiz, "--assunto", "a")
    git(raiz, "add", "wip.py"); git(raiz, "commit", "-qm", "wip")  # mesmo conteúdo, agora commitado
    c = conferir(raiz, snap_de(r))
    assert c.returncode == 0, c.stdout
    (raiz / "wip.py").write_text("mudou\n")
    assert conferir(raiz, snap_de(r)).returncode == 2


def test_conferir_handoff_antigo_sem_bloco(tmp_path):
    raiz = repo(tmp_path)
    hist = raiz / "handoffs/history"; hist.mkdir(parents=True)
    (hist / "2026-01-01T000000Z-velho.md").write_text(CORPO)
    c = conferir(raiz, "handoffs/history/2026-01-01T000000Z-velho.md")
    assert c.returncode == 3 and "sem bloco de estado" in c.stdout


def test_indexar_nao_altera_snapshot_existente(tmp_path):
    raiz = repo(tmp_path)
    hist = raiz / "handoffs/history"; hist.mkdir(parents=True)
    p = hist / "2026-01-01T000000Z-x.md"
    p.write_text(CORPO)
    rodar(raiz, "--assunto", "x", "--indexar", "handoffs/history/2026-01-01T000000Z-x.md")
    assert p.read_text() == CORPO


def test_sem_git_grava_hash_dos_citados_e_confere(tmp_path):
    (tmp_path / "nota.md").write_text("a\n")
    r = rodar(tmp_path, "--assunto", "a", "--sem-commit", corpo=com_citacao("nota.md"))
    assert "commit: sem git" in (tmp_path / snap_de(r)).read_text()
    assert conferir(tmp_path, snap_de(r)).returncode == 0
    (tmp_path / "nota.md").unlink()
    c = conferir(tmp_path, snap_de(r))
    assert c.returncode == 2 and "sumiu" in c.stdout


def test_bloco_escrito_a_mao_e_descartado(tmp_path):
    raiz = repo(tmp_path)
    falso = CORPO + "<!-- handoff-estado:inicio -->\n- commit: deadbeef\n<!-- handoff-estado:fim -->\nfim\n"
    txt = (raiz / snap_de(rodar(raiz, "--assunto", "a", corpo=falso))).read_text()
    assert txt.count("handoff-estado:inicio") == 1 and "deadbeef" not in txt and "fim\n" in txt
