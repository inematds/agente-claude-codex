# Handoff — 2026-09-16
## Projeto e escopo
agente-claude-codex: kit de migração / workspace agnóstico. Esta sessão: itens 1-4 da evolução (Fase 0, piloto de skill, 4 destinos, automação, memória).
## Objetivo atual
Ver tasks/current.md: aplicar a migração nos 13 projetos trusted e promover memória em projeto real.
## Estado aceito
- `~/.codex/AGENTS.md` existe (75 linhas), gerado do CLAUDE.md global; fonte de verdade continua o CLAUDE.md, `drift-instructions.sh` vigia.
- MCP magnific e metricool registrados no Codex (`codex mcp list`: enabled, **Not logged in**; login OAuth é ação do usuário).
- Skills canônicas `session-handoff` e `prime` em `skills/`, instaladas em claude, codex, dsh e v3; `drift` = ok nos 4.
- 3 skills do dsh (formato-curso-v2, v5, capa-inema) espelhadas da fonte em formato-curso-inema; `mirror-drift` = ok.
- Scripts novos: migrar-projeto, faxina, drift-report, drift-instructions, promover-memoria. Todos rodados ao menos uma vez.
## Arquivos alterados
scripts/sync-skills.sh (reescrito: 4 destinos, mirror, backup fora de skills/), scripts/audit.sh (dsh/v3), 5 scripts novos, skills/, README.md, PLANO.md, FALHAS.md, context/, tasks/, este arquivo. Fora do repo: ~/.codex/AGENTS.md, ~/.codex/config.toml (mcp_servers), skills instaladas nos 4 destinos.
## Checks rodados e resultado
- readback Fase 0 (codex exec em ~/projetos/wifi) — passou: citou AGENTS.md:7, :21, :31.
- prime em sessão nova do Codex neste repo — passou (briefing com fontes; apontou contradições entre handoff antigo e tarefa, agora reconciliadas).
- sync-skills drift — passou (8/8 ok); mirror-drift — passou.
- migrar-projeto.sh ~/projetos/wifi --faxina (audit) — passou; propostos removidos depois.
- promover-memoria.sh em rascunho com 50 memórias do timesmkt3 — passou (3 propostas, 1 aprovada).
- drift-report.sh — passou, sem drift.
- readback no dsh — **não rodado** (dsh só tem painel web; ver PLANO §8).
## Perguntas abertas
- Fazer login OAuth dos MCP no Codex (`codex mcp login magnific`, `codex mcp login metricool`)?
- Qual dos 13 projetos trusted aplicar primeiro com `migrar-projeto.sh --aplicar`? Sugestão: wifi (CLAUDE.md de 21 linhas, sem git) ou portal.
- Instalar o cron semanal do drift-report?
## Próxima ação exata
`scripts/migrar-projeto.sh ~/projetos/<piloto> --aplicar` e depois `scripts/promover-memoria.sh ~/projetos/<piloto> --n 3`.
