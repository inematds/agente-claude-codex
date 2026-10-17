# Falhas (mais recente no topo)

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-10-17 | `/prime` sem argumento abria o handoff mais novo do projeto; com várias sessões no mesmo projeto (wifi tinha 12 assuntos abertos), a sessão nova pegava o de outra | `handoff-grava.py` imprime `/clear` + `/prime <snapshot exato>`; prime aceita o caminho; hook 1.7.1 cita o da sessão | infra |
| 2026-10-13 | menu do guia estourava 84–371 px entre 800 e 1024 e quebrava os rótulos em 2–3 linhas até 1440 (8 links não cabem na `.wrap` de 1160 px); só tinha sido medido em 360/1280 | `white-space:nowrap` no nav, 4 links secundários ocultos (`.sec2`), links somem < 1240 px; medido 390–1920 nos 3 idiomas | prompt |
| 2026-10-05 | handoff da sessão MODS ficou só no chat: `~/projetos/wifi` tem só `CLAUDE.md` (sem `handoffs/` nem `AGENTS.md`), o session-handoff não gravou e o `/prime` seguinte não achou nada | condição de gravar inclui `CLAUDE.md` + `mkdir -p handoffs/history` | prompt |
| 2026-09-27 | sync-skills apontava o Codex para `~/.codex/skills` (o Codex lê `~/.agents/skills` desde 2026-09-24) e o drift marcava "não instalada" falso | `dest_of codex` → `~/.agents/skills`, sem cópia dupla | infra |
| 2026-09-27 | guia com rolagem horizontal em 360px: coluna `1fr` do `.step` crescia com o `<pre>`; nav estourava | `.step>div,.grid>.card{min-width:0}` + nav compacto < 600px | prompt |
| 2026-09-16 | sync-skills install com destino já existente copiava a skill para DENTRO da pasta (session-handoff/session-handoff) e o drift nunca zerava | `rm -rf "$dest"` antes do `cp -a` | prompt |
| 2026-09-16 | backup da skill gravado dentro de `~/.claude/skills/` aparecia como skill nova no Claude | backup em `~/.claude/skills-backup/`, fora da pasta de skills | prompt |
| 2026-09-13 | readback-test.sh forçava `-s read-only` no codex exec; bwrap falha por AppArmor neste host | remover o flag, respeitar sandbox_mode do config.toml | prompt \| infra |
| 2026-09-13 | resumo do audit.sh contava linhas da seção 3 (73+17+4=94 ≠ 89) | restringir grep à seção 2.1 | prompt |
