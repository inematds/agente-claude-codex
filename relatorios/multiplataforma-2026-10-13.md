# Teste do modelo multiplataforma — 2026-10-13

Projeto novo criado com `scripts/init-core.sh` numa pasta de teste; `context/overview.md` preenchido (padaria fictícia); remoto `origin` = repositório bare local no lugar do GitHub. Bloco de `template/plataformas/instrucoes-projeto.md` colado igual nos dois runtimes.

1. `check.sh` → 8 arquivos `[ok]`.
2. **Codex** (`codex exec -m gpt-6-astra`), tarefa "crie context/voz.md com 3 linhas e siga ESCREVER" → commit `27b5b47` + push no origin/main.
3. **Claude** (`claude -p`), tarefa "leia context/voz.md (criado por outra IA), acrescente a 4ª linha sobre emojis e siga ESCREVER" → leu as 3 linhas do Codex, conferiu com o overview, commit `c404c67` + push.
4. `git log` do origin: `608998c init` → `27b5b47` (Codex) → `c404c67` (Claude). Arquivo final com 4 linhas.

Não testado aqui: conectores GitHub do Claude.ai e do ChatGPT (dependem da conta); o bloco é o mesmo, o teste de ida e volta fica no `plataformas/README.md`.
