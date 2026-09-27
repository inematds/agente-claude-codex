# 2026-09-27 — Histórico de handoff sem sobrescrever; latest.md continua cópia integral

## Decisão
- `session-handoff` grava cada handoff num arquivo novo `handoffs/history/AAAA-MM-DDTHHMMSSZ.md` (UTC, sufixo `-2`, `-3` em colisão, criação exclusiva). Snapshot antigo nunca é editado nem apagado.
- `handoffs/latest.md` **continua sendo a cópia integral** do último snapshot, não um ponteiro de uma linha.
- `prime` aceita os dois formatos: cópia integral (este kit) e ponteiro de uma linha para `handoffs/history/*.md` (kit "Use Both"), validando o caminho.

## Por quê cópia e não ponteiro
Todos os consumidores atuais leem `latest.md` como documento:
- `scripts/readback-test.sh` avalia se a sessão nova cita o conteúdo de `handoffs/latest.md`;
- `template/scripts/check.sh` só exige que `handoffs/latest.md` exista e não esteja vazio;
- `template/AGENTS.md`, `scripts/adapt-instructions.sh` e `scripts/migrar-projeto.sh` mandam o agente ler `latest.md` na ordem de leitura;
- agentes sem a skill `prime` (Gemini, OpenCode, modelo local) abrem `latest.md` direto e não seguiriam um ponteiro.

Um ponteiro quebraria esses leitores ou exigiria mudar todos. A cópia custa um arquivo duplicado por sessão e dá o mesmo ganho que importa: nenhum handoff se perde.

## Origem
Adaptado do kit MIT "Use Both: Claude + Codex Workflow Kit" (Prompt Advisers / Mark Kashef), que usa `handoff/history/` + `handoff/LATEST.md` como ponteiro. Guia: https://inematds.github.io/use-both-claude-codex/guia/
