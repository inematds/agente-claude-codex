# Tarefa atual
- Objetivo: validar o piloto — skill `session-handoff` portada pro Codex via polyskill e readback passando nos dois runtimes.
- Dono: Nei (decide piloto e skills); agente executa.
- Critério de pronto: `scripts/readback-test.sh . both` gera respostas que citam AGENTS.md/tasks/handoffs em ambos; `scripts/sync-skills.sh drift` sem DRIFT.
- Próxima ação concreta: Fase 0 do plano em `~/projetos/wifi/DIAGNOSTICO-CLAUDE-CODEX-2026-09-14.md` — `scripts/adapt-instructions.sh ~/.claude`, revisar, gravar `~/.codex/AGENTS.md`, readback em `~/projetos/wifi`. Depois Fase 1 (`sync-skills.sh import session-handoff`, com destinos --dsh e --v3 a acrescentar).
- Bloqueios: nenhum (publicação já feita; docs/ segue fora do git por decisão tácita).
