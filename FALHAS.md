# Falhas (mais recente no topo)

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-09-16 | sync-skills install com destino já existente copiava a skill para DENTRO da pasta (session-handoff/session-handoff) e o drift nunca zerava | `rm -rf "$dest"` antes do `cp -a` | prompt |
| 2026-09-16 | backup da skill gravado dentro de `~/.claude/skills/` aparecia como skill nova no Claude | backup em `~/.claude/skills-backup/`, fora da pasta de skills | prompt |
| 2026-09-13 | readback-test.sh forçava `-s read-only` no codex exec; bwrap falha por AppArmor neste host | remover o flag, respeitar sandbox_mode do config.toml | prompt \| infra |
| 2026-09-13 | resumo do audit.sh contava linhas da seção 3 (73+17+4=94 ≠ 89) | restringir grep à seção 2.1 | prompt |
