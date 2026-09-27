# Estado atual — 2026-09-27
- Última sessão: v1.1.0 — melhorias do kit "Use Both" (prime endurecido, handoff com histórico, instalador em prévia com teste, prompts/guia "usar os dois juntos", guia trilíngue).
- O que funciona: todos os scripts de `scripts/`; `tests/test-sync-skills.sh` 20/20; AGENTS.md global do Codex.
- Pendente: **instalar a v1.1.0 das skills** nos destinos (o dono decide: `scripts/sync-skills.sh install <skill> --all --apply --replace`; hoje o drift marca DRIFT nos 4 porque os destinos têm a versão de 2026-09-16); aplicar migração em projeto real; login OAuth dos MCP no Codex; readback no dsh; cron do drift-report.
- Fatos que mudaram: destino do Codex no sync-skills passou a ser `~/.agents/skills`; handoffs agora ficam em `handoffs/history/` com cópia em `handoffs/latest.md`.
