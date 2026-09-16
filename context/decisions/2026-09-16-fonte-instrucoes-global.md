# Decisão: fonte das instruções globais continua o CLAUDE.md
- Data: 2026-09-16 | Status: aceita | Fonte: sessão de evolução do kit
## Contexto
O plano previa CLAUDE.md global virar `@AGENTS.md` + resíduo. Mudar o CLAUDE.md global altera o setup Claude em produção do usuário.
## Decisão
`~/.claude/CLAUDE.md` segue como fonte; `~/.codex/AGENTS.md` é gerado dele por `adapt-instructions.sh` e `drift-instructions.sh` avisa quando divergirem. Inverter a fonte fica para quando o Codex for usado em paridade.
## Consequências
Duas cópias, uma vigiada. Regerar o AGENTS.md sempre que o CLAUDE.md mudar.
