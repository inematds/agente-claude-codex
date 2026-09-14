# Handoff — 2026-09-13
## Projeto e escopo
agente-claude-codex: kit de migração / workspace agnóstico. Escopo desta sessão: criar o repo, plano, prompts, scripts, template e primeira evidência.
## Objetivo atual
Ver tasks/current.md: validar piloto (session-handoff no Codex + readback nos dois runtimes).
## Estado aceito
Repo criado, 2 commits, branch main, sem remote. Auditoria rodada (relatorios/auditoria-2026-09-13.md). Readback aprovado no Codex e no Claude. Nada em ~/.claude ou ~/.codex alterado.
## Arquivos alterados
PLANO.md, README.md, AGENTS.md, CLAUDE.md, prompts/*, scripts/*, template/*, context/*, tasks/current.md, .gitignore, este arquivo.
## Checks rodados e resultado
- scripts/audit.sh — passou (89 skills só no Claude: 71 reutilizáveis, 15 adaptador, 2 nativo, 1 sem SKILL.md).
- scripts/adapt-instructions.sh ~/.claude --dry-run — passou (71 linhas portáteis, 7 resíduo Claude).
- template/scripts/check.sh — passou.
- scripts/readback-test.sh . codex — **passou** na 2ª rodada (1ª falhou por sandbox bwrap: script forçava `-s read-only`; corrigido). Codex citou AGENTS.md, PLANO.md, tasks/current.md e apontou 3 inconsistências reais, todas corrigidas nesta sessão.
- scripts/readback-test.sh . claude — **passou**: respondeu as 5 perguntas citando AGENTS.md, context/decisions, tasks/current.md e handoffs/latest.md; apontou edições não commitadas, branch master e ausência de remote (corrigidos os dois primeiros neste commit).
- scripts/sync-skills.sh — **não rodado** (aguarda escolha do piloto).
- Cópia isolada + check.sh — **não rodado**.
## Perguntas abertas
- Qual projeto real é o piloto? (default: este repo)
- docs/ no git: repo privado, ou só reescritas próprias?
- Publicar em inematds/agente-claude-codex?
## Próxima ação exata
`scripts/sync-skills.sh import session-handoff && scripts/sync-skills.sh build`, depois `install session-handoff --codex` e `drift`.
