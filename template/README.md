# <nome do projeto>

Onboarding humano. O agente lê `AGENTS.md` primeiro.

## Como rodar
## Como testar
## Estrutura
- `context/` — conhecimento durável (overview, current-state, sources, decisions/)
- `tasks/current.md` — o que está sendo feito, dono, critério de pronto
- `handoffs/latest.md` — continuação para a próxima sessão (cópia do último snapshot)
- `handoffs/history/` — um snapshot por handoff, nunca sobrescrito
- `.agents/skills/` — skills canônicas
- `scripts/` — comandos reproduzíveis
- `plataformas/` — como usar este mesmo contexto no Claude.ai, ChatGPT, Codex e Gemini (instruções para colar + teste)
- `CLAUDE.md`, `GEMINI.md` — só apontam para `AGENTS.md`
