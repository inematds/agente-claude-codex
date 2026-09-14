# Tarefa atual
- Objetivo: validar o piloto — skill `session-handoff` portada pro Codex via polyskill e readback passando nos dois runtimes.
- Dono: Nei (decide piloto e skills); agente executa.
- Critério de pronto: `scripts/readback-test.sh . both` gera respostas que citam AGENTS.md/tasks/handoffs em ambos; `scripts/sync-skills.sh drift` sem DRIFT.
- Próxima ação concreta: dono escolhe projeto piloto e confirma publicação (privado/público); depois rodar `scripts/sync-skills.sh import session-handoff`.
- Bloqueios: decisão do dono sobre piloto e sobre docs/ no git.
