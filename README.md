# agente-claude-codex

Kit pra migrar um setup Claude Code pro Codex **ou** deixar o trabalho independente de modelo: separar o "cérebro" (contexto, decisões, tarefas, handoffs, skills) do executor (Claude, Codex, Gemini, local).

Baseado na newsletter "Como migrar do Claude para o Codex — ou ficar independente de modelo" e na prompt library "Model-agnostic workspaces" (07 SEP 2026). Leia `PLANO.md` primeiro.

## O que tem aqui
| Pasta | Conteúdo |
|---|---|
| `PLANO.md` | análise dos docs + auditoria desta máquina + passos e critérios de aceite |
| `prompts/` | Prompt A (migrar), Prompt B (workspace portátil), readback/handoff, quick-starts, em texto copiável |
| `scripts/audit.sh` | inventário somente leitura Claude x Codex → matriz reutilizável / adaptador / nativo |
| `scripts/adapt-instructions.sh` | CLAUDE.md → AGENTS.md (portátil) + CLAUDE.md (`@AGENTS.md` + resíduo) |
| `scripts/sync-skills.sh` | import / build / install / drift de skills via polyskill (uma fonte canônica) |
| `scripts/readback-test.sh` | teste de continuidade: sessão nova em cada runtime responde as 5 perguntas |
| `template/` | núcleo portátil pra copiar em qualquer projeto (AGENTS.md, context/, tasks/, handoffs/, .agents/skills/, scripts/check.sh) |
| `relatorios/` | saída das auditorias e readbacks |
| `docs/` | material de origem (local, fora do git) |

## Uso rápido
```bash
scripts/audit.sh                                   # 1. inventário
scripts/adapt-instructions.sh ~/projetos/meu-projeto   # 2. instruções portáteis (gera *.proposto.md)
cp -r template/. ~/projetos/meu-projeto/           # 3. núcleo portátil (não sobrescreve nada que exista? — confira antes)
scripts/sync-skills.sh import session-handoff && scripts/sync-skills.sh build && scripts/sync-skills.sh install session-handoff --both
scripts/readback-test.sh ~/projetos/meu-projeto both   # 4. prova
```

## Regras
- Modo audit antes de implement. Nada em `~/.claude` ou `~/.codex` é copiado em massa ou apagado.
- Segredos nunca entram no repo; keys ficam em `~/projetos/openpcbotv2/.env` e são referenciadas, não copiadas.
