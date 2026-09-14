# Falhas (mais recente no topo)

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-09-13 | readback-test.sh forçava `-s read-only` no codex exec; bwrap falha por AppArmor neste host | remover o flag, respeitar sandbox_mode do config.toml | prompt \| infra |
| 2026-09-13 | resumo do audit.sh contava linhas da seção 3 (73+17+4=94 ≠ 89) | restringir grep à seção 2.1 | prompt |
