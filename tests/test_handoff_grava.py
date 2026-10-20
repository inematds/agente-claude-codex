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
    return [ln.split("\t")[0] for ln in r.stdout.splitlines() if ln and not ln.endswith("\tparado")]


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


def test_latest_aponta_o_mais_novo_sem_copiar_o_corpo(tmp_path):
    rodar(tmp_path, "--assunto", "a", "--sem-commit")
    r = rodar(tmp_path, "--assunto", "b", "--sem-commit", corpo="# Handoff — Título B\n\n" + CORPO + "MARCA-B\n")
    snap = re.search(r"snapshot: (\S+)", r.stdout)[1]
    txt = (tmp_path / "handoffs/latest.md").read_text()
    assert "MARCA-B" not in txt and f"Mais recente: `{snap}` — Título B" in txt
    assert len(txt) < 1200  # só índice + ponteiro


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


def test_arquivo_ilegivel_nao_derruba_a_gravacao(tmp_path):
    import pytest
    if os.geteuid() == 0:
        pytest.skip("root lê tudo")
    raiz = repo(tmp_path)
    trava = raiz / "trava.bin"
    trava.write_text("x")
    trava.chmod(0)
    try:
        r = rodar(raiz, "--assunto", "a", corpo=com_citacao("trava.bin"))
        assert "sha256:ilegivel" in (raiz / snap_de(r)).read_text()
        assert conferir(raiz, snap_de(r)).returncode == 0
    finally:
        trava.chmod(0o644)


def test_imprime_comando_de_retomada_com_o_snapshot_exato(tmp_path):
    r = rodar(tmp_path, "--assunto", "robot", "--sem-commit")
    snap = re.search(r"snapshot: (handoffs/history/\S+)", r.stdout)[1]
    linhas = r.stdout.splitlines()
    assert linhas[-2:] == ["  /clear", f"  /prime {snap}"]
    # outra sessão grava depois no mesmo projeto: o comando desta continua apontando o seu
    r2 = rodar(tmp_path, "--assunto", "outro", "--sem-commit")
    assert f"/prime {snap}" not in r2.stdout


def test_fechado_nao_imprime_comando_de_retomada(tmp_path):
    r = rodar(tmp_path, "--assunto", "robot", "--sem-commit", "--fechado")
    assert "/prime" not in r.stdout


def _outro_repo(tmp_path):
    o = tmp_path / "outro"
    o.mkdir()
    repo(o)
    (o / "curso.html").write_text("v1")
    return o


def test_repo_do_trabalho_entra_no_bloco_e_no_conferir(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    repo(proj)
    o = _outro_repo(tmp_path)
    r = rodar(proj, "--assunto", "robot", "--repo", str(o))
    snap = re.search(r"snapshot: (handoffs/history/\S+)", r.stdout)[1]
    txt = (proj / snap).read_text()
    assert f"### Repo do trabalho: {o}" in txt and "`curso.html` · sha256:" in txt
    assert rodar(proj, "--conferir", snap).returncode == 0
    (o / "curso.html").write_text("v2")  # trabalho mudou no outro repo
    c = rodar(proj, "--conferir", snap, ok=False)
    assert c.returncode == 2 and f"{o}: curso.html" in c.stdout


def test_repo_invalido_e_recusado(tmp_path):
    (tmp_path / "nao-git").mkdir()
    r = rodar(tmp_path, "--assunto", "x", "--sem-commit", "--repo", str(tmp_path / "nao-git"), ok=False)
    assert r.returncode != 0 and "--repo" in r.stderr


def test_avisa_repo_citado_sem_opcao(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    o = _outro_repo(tmp_path)
    r = rodar(proj, "--assunto", "x", "--sem-commit", corpo=CORPO + f"Trabalho em `{o}/curso.html`\n")
    assert "aviso:" in r.stdout and str(o) in r.stdout and "--repo" in r.stdout
    r2 = rodar(proj, "--assunto", "y", "--sem-commit", "--repo", str(o), corpo=CORPO + f"`{o}/curso.html`\n")
    assert "--repo" not in r2.stdout


def test_avisa_handoff_sem_perguntas_teste(tmp_path):
    r = rodar(tmp_path, "--assunto", "x", "--sem-commit")
    assert "aviso: handoff sem a seção Perguntas-teste" in r.stdout
    r2 = rodar(tmp_path, "--assunto", "y", "--sem-commit", corpo=CORPO + "\n## Perguntas-teste\n1. a → b — fonte: `x`\n")
    assert "aviso: handoff sem" not in r2.stdout


def test_avisa_handoff_sem_nao_fazer(tmp_path):
    r = rodar(tmp_path, "--assunto", "x", "--sem-commit")
    assert "aviso: falta a seção Não fazer" in r.stdout
    r2 = rodar(tmp_path, "--assunto", "y", "--sem-commit",
               corpo=CORPO + "\n## Não fazer (restrições e travas)\n- não publicar — fonte: `x`\n")
    assert "Não fazer" not in r2.stdout


def test_repo_com_mais_de_200_sujos_fica_igual_e_acusa_mudanca(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    o = _outro_repo(tmp_path)
    for i in range(210):
        (o / f"f{i:03}.txt").write_text(str(i))
    snap = re.search(r"snapshot: (\S+)", rodar(proj, "--assunto", "x", "--sem-commit", "--repo", str(o)).stdout)[1]
    r = rodar(proj, "--conferir", snap)
    assert "igual" in r.stdout and str(o) in r.stdout
    (o / "f209.txt").write_text("mudou")  # fora da lista gravada (só as 200 primeiras)
    c = rodar(proj, "--conferir", snap, ok=False)
    assert c.returncode == 2 and "fora da lista gravada" in c.stdout


# --- 1.9.3: trava do índice (vários terminais) e assuntos parados ---

def _envelhecer(raiz, slug, dias):
    for p in (raiz / "handoffs/history").glob(f"*-{slug}.md"):
        t = time.time() - dias * 86400
        os.utime(p, (t, t))


def _bloco(raiz, ini, fim):
    txt = (raiz / "handoffs/latest.md").read_text(encoding="utf-8")
    if ini not in txt:
        return ""
    return txt.split(ini, 1)[1].split(fim, 1)[0]


def test_oito_terminais_ao_mesmo_tempo_nao_perdem_linha(tmp_path):
    raiz = repo(tmp_path)
    procs = [subprocess.Popen([sys.executable, str(SCRIPT), "--raiz", str(raiz), "--assunto", f"t{i}"],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
             for i in range(8)]
    for p in procs:
        p.stdin.write(CORPO)
        p.stdin.close()
    for p in procs:
        p.wait(timeout=120)
        assert p.returncode == 0, p.stderr.read()
    assert sorted(indice(raiz)) == [f"t{i}" for i in range(8)]
    assert int(git(raiz, "rev-list", "--count", "HEAD").strip()) == 9  # base + 8 handoffs


def test_assunto_parado_sai_dos_abertos_e_volta_ao_gravar(tmp_path):
    rodar(tmp_path, "--assunto", "velho", "--sem-commit")
    _envelhecer(tmp_path, "velho", 5)
    r = rodar(tmp_path, "--assunto", "novo", "--sem-commit")
    assert indice(tmp_path) == ["novo"]
    assert "velho" in _bloco(tmp_path, "<!-- handoff-parados:inicio -->", "<!-- handoff-parados:fim -->")
    assert "velho" not in _bloco(tmp_path, "<!-- handoff-indice:inicio -->", "<!-- handoff-indice:fim -->")
    assert "parado" in r.stdout
    lst = rodar(tmp_path, "--listar").stdout
    assert re.search(r"^velho\t\S+\t.+\tparado$", lst, re.M)  # slug continua achável para reusar
    rodar(tmp_path, "--assunto", "velho", "--sem-commit")
    assert indice(tmp_path) == ["velho", "novo"]
    assert "velho" not in _bloco(tmp_path, "<!-- handoff-parados:inicio -->", "<!-- handoff-parados:fim -->")
    assert len(list((tmp_path / "handoffs/history").glob("*.md"))) == 3  # nada apagado


def test_fechado_tira_assunto_dos_parados(tmp_path):
    rodar(tmp_path, "--assunto", "velho", "--sem-commit")
    _envelhecer(tmp_path, "velho", 5)
    rodar(tmp_path, "--assunto", "novo", "--sem-commit")
    rodar(tmp_path, "--assunto", "velho", "--fechado", "--sem-commit")
    assert "velho" not in (tmp_path / "handoffs/latest.md").read_text(encoding="utf-8").split("Cópia integral")[0]


def test_parado_dias_zero_desliga_a_limpeza(tmp_path):
    rodar(tmp_path, "--assunto", "velho", "--sem-commit")
    _envelhecer(tmp_path, "velho", 30)
    rodar(tmp_path, "--assunto", "novo", "--sem-commit", "--parado-dias", "0")
    assert indice(tmp_path) == ["novo", "velho"]


def test_parados_tem_teto(tmp_path):
    hist = tmp_path / "handoffs/history"
    hist.mkdir(parents=True)
    linhas = []
    for i in range(60):
        p = hist / f"2026-01-01T0000{i:02}Z-s{i}.md"
        p.write_text(CORPO)
        t = time.time() - (10 + i) * 86400
        os.utime(p, (t, t))
        linhas.append(f"- `s{i}` · handoffs/history/{p.name} · 01/01 00:00")
    (tmp_path / "handoffs/latest.md").write_text(
        "# x\n\n<!-- handoff-indice:inicio -->\n" + "\n".join(linhas) + "\n<!-- handoff-indice:fim -->\n")
    rodar(tmp_path, "--assunto", "novo", "--sem-commit")
    par = _bloco(tmp_path, "<!-- handoff-parados:inicio -->", "<!-- handoff-parados:fim -->")
    assert par.count("- `s") == 50 and "`s0`" in par and "`s59`" not in par  # fica o mais recente
    assert len(list(hist.glob("*.md"))) == 61


# --- 1.10.3: lista de fechados (handoffs/fechados.md) para pesquisa ---

def _fechados(raiz):
    p = raiz / "handoffs/fechados.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def test_fechado_vai_para_fechados_md_com_titulo(tmp_path):
    rodar(tmp_path, "--assunto", "rea-es", "--sem-commit")
    rodar(tmp_path, "--assunto", "rea-es", "--fechado", "--sem-commit", corpo="# Handoff — Curso REA em espanhol\n\n" + CORPO)
    f = _fechados(tmp_path)
    assert re.search(r"^- `rea-es` · handoffs/history/\S+-rea-es(-\d+)?\.md · \d{2}/\d{2}/\d{4} \d{2}:\d{2} · Curso REA em espanhol$", f, re.M)
    assert "rea-es" not in (tmp_path / "handoffs/latest.md").read_text(encoding="utf-8").split("Cópia integral")[0]
    lst = rodar(tmp_path, "--fechados").stdout
    assert lst.startswith("rea-es\t") and "Curso REA em espanhol" in lst


def test_reabrir_tira_dos_fechados(tmp_path):
    rodar(tmp_path, "--assunto", "x", "--fechado", "--sem-commit")
    assert "`x`" in _fechados(tmp_path)
    rodar(tmp_path, "--assunto", "x", "--sem-commit")
    assert "`x`" not in _fechados(tmp_path) and indice(tmp_path) == ["x"]


def test_commit_leva_fechados_md(tmp_path):
    raiz = repo(tmp_path)
    rodar(raiz, "--assunto", "x", "--fechado")
    assert "handoffs/fechados.md" in git(raiz, "show", "--name-only", "--format=", "HEAD").split()


def test_recuperar_fechados_pelo_git_log(tmp_path):
    raiz = repo(tmp_path)
    rodar(raiz, "--assunto", "velho", "--fechado", corpo="# Handoff — Trabalho antigo\n\n" + CORPO)
    (raiz / "handoffs/fechados.md").unlink()  # simula fechado gravado antes da 1.10.3
    git(raiz, "commit", "-qam", "apaga")
    rodar(raiz, "--assunto", "novo", "--sem-commit")
    assert "velho" not in _fechados(raiz)
    r = rodar(raiz, "--recuperar-fechados", "--sem-commit")
    assert "1 fechado(s) recuperado(s)" in r.stdout
    assert "`velho`" in _fechados(raiz) and "Trabalho antigo" in _fechados(raiz)
    r2 = rodar(raiz, "--recuperar-fechados", "--sem-commit")
    assert "0 fechado(s) recuperado(s)" in r2.stdout  # não duplica


def test_arrumar_move_parados_e_recupera_fechados_sem_snapshot_novo(tmp_path):
    raiz = repo(tmp_path)
    rodar(raiz, "--assunto", "fim", "--fechado", corpo="# Handoff — Já entregue\n\n" + CORPO)
    (raiz / "handoffs/fechados.md").unlink()
    git(raiz, "commit", "-qam", "apaga")
    rodar(raiz, "--assunto", "velho")
    rodar(raiz, "--assunto", "vivo")
    _envelhecer(raiz, "velho", 5)
    n = len(list((raiz / "handoffs/history").glob("*.md")))
    r = rodar(raiz, "--arrumar")
    assert indice(raiz) == ["vivo"] and "`velho`" in _bloco(raiz, "<!-- handoff-parados:inicio -->", "<!-- handoff-parados:fim -->")
    assert "`fim`" in _fechados(raiz)
    assert len(list((raiz / "handoffs/history").glob("*.md"))) == n
    assert "handoffs/fechados.md" in git(raiz, "show", "--name-only", "--format=", "HEAD").split()
    assert "nada a arrumar" in rodar(raiz, "--arrumar").stdout


def test_arrumar_tira_copia_integral_antiga(tmp_path):
    raiz = repo(tmp_path)
    rodar(raiz, "--assunto", "a")
    lt = raiz / "handoffs/latest.md"
    lt.write_text(lt.read_text().split("\n---\n")[0] + "\n---\n\nCópia integral do snapshot mais recente (x):\n\nCORPO-VELHO\n")
    git(raiz, "commit", "-qam", "formato antigo")
    rodar(raiz, "--arrumar")
    txt = lt.read_text()
    assert "CORPO-VELHO" not in txt and "Mais recente:" in txt and indice(raiz) == ["a"]
