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
