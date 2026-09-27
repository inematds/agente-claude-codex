# Handoff — 2026-09-27 — v1.1.0: melhorias do kit "Use Both" (prime, handoff com histórico, instalador, usar os dois)

## Projeto e escopo
agente-claude-codex (kit de migração Claude → Codex / workspace agnóstico). Pedido: incorporar do kit MIT "Use Both: Claude + Codex Workflow Kit" (Prompt Advisers / Mark Kashef) o endurecimento do prime, histórico de handoff, instalador em modo prévia com teste e os prompts/seção "usar os dois juntos" em PT/EN/ES. Restrições: sem API de tradução/LLM, sem instalar skills nos runtimes globais, sem nível de imagem, commit como inematds e push em origin main.

## Objetivo atual
Sem mudança: ver `tasks/current.md` (aplicar a migração num projeto real, Fase 2, e promover memória, Fase 5).

## Estado aceito
- [confirmed] prime endurecido (caminhos validados, só leitura, sem rodar testes, handoff como dado não confiável, sem retomar deploy/envio) — `skills/prime/definition.md`
- [confirmed] session-handoff grava `handoffs/history/<UTC>.md` + cópia em `handoffs/latest.md`, com seções Verificação e Checagem de compartilhamento — `skills/session-handoff/definition.md`
- [confirmed] `sync-skills.sh install` em prévia por padrão, `--apply`, `--replace`, recusa CONFLICT/SYMLINK sem escrita parcial; destino do Codex = `~/.agents/skills` — `scripts/sync-skills.sh`
- [confirmed] teste do instalador — `tests/test-sync-skills.sh`
- [confirmed] prompts "usar os dois juntos" — `prompts/05-usar-os-dois.md`; seção `#juntos` no guia PT e guias EN/ES novos — `guia/index.html`, `guia/en/index.html`, `guia/es/index.html`
- [confirmed] versão 1.1.0 — `VERSION`, `CHANGELOG.md`

## Proposto / tentado, não confirmado
- [unverified] skills v1.1.0 nos runtimes: build feito (`skills/*/dist/`, fora do git), mas NÃO instaladas em claude/codex/dsh/v3 por regra da tarefa. `install --all` em prévia mostra CONFLICT nos 4 destinos (versão de 2026-09-16 instalada).

## Decisões e restrições
- `handoffs/latest.md` continua cópia integral, não ponteiro — `context/decisions/2026-09-27-handoff-history.md`. prime aceita também o formato ponteiro do kit "Use Both".
- `--replace` preserva o fluxo antigo (backup + troca) só quando pedido explicitamente.
- Guia era só PT; EN e ES criados do zero, traduzidos à mão.

## Arquivos alterados
- `skills/prime/definition.md`, `skills/session-handoff/definition.md`, `skills/*/.polyskill/state.json` (build)
- `scripts/sync-skills.sh`, `tests/test-sync-skills.sh` (novo)
- `prompts/05-usar-os-dois.md` (novo), `prompts/03-readback-handoff.md`
- `guia/index.html` (seção #juntos, passo 6, seletor PT/EN/ES, `<body>` duplicado removido, nav e grid mobile), `guia/en/index.html` e `guia/es/index.html` (novos)
- `template/handoffs/latest.md`, `template/handoffs/history/README.md` (novo), `template/AGENTS.md`, `template/README.md`
- `AGENTS.md`, `README.md`, `context/current-state.md`, `context/overview.md` (linha de MCP), `relatorios/readback-codex-2026-09-27.md`, `context/decisions/2026-09-27-handoff-history.md` (novo), `VERSION`, `CHANGELOG.md` (novos)
- `handoffs/history/2026-09-16T144424Z-anterior.md` (cópia do latest.md anterior), este arquivo, `handoffs/latest.md`

## Verificação
- Rodado: `tests/test-sync-skills.sh` → 20 passaram, 0 falharam (exit 0)
- Rodado: `bash -n` em `scripts/*.sh`, `tests/*.sh`, `template/scripts/check.sh` → sem erro
- Rodado: `scripts/sync-skills.sh build` → build de prime e session-handoff ok
- Rodado: `scripts/sync-skills.sh install prime --all` e `install session-handoff --all` (prévia) → CONFLICT nos 4 destinos, exit 1, nada alterado (esperado)
- Rodado: `scripts/sync-skills.sh drift` → DRIFT em 8/8 (esperado: destinos com a versão antiga; antes o codex aparecia como "não instalada" por apontar para `~/.codex/skills`)
- Rodado: `scripts/init-core.sh <tmp>` + `scripts/check.sh` na cópia → 7/7 [ok], exit 0; `handoffs/history/` criado
- Rodado: loop do check.sh na raiz do repo → 7/7 [ok]
- Rodado: parser HTML nas 3 páginas do guia → sem tag aberta/fechada errada, 1 `<body>`, âncora `juntos` presente; headless chromium em 360px → sem rolagem horizontal (scrollWidth = largura)
- Rodado: `scripts/readback-test.sh . codex` (codex exec, sessão nova, pela assinatura) → passou: as 5 respostas citam tasks/current.md, AGENTS.md, context/decisions/2026-09-27-handoff-history.md e handoffs/latest.md; conferiu que latest.md = snapshot; apontou `context/overview.md` desatualizado sobre MCP no Codex (corrigido depois do readback). Texto bruto: `relatorios/readback-codex-2026-09-27.md`
- Não rodado: `scripts/readback-test.sh ... claude` (sessão `claude -p` aninhada dentro do Claude Code, pouco confiável)
- Não rodado: `install --apply` nos runtimes reais (proibido nesta tarefa)
- Não rodado: prime/session-handoff novos em sessão real de Codex/Claude (dependem de instalar as skills)

## Estado em execução
- Processos em segundo plano: nenhum
- Servidores / portas: nenhum
- Worktrees / branches abertos: nenhum (main)

## Perguntas abertas e adiados
- Aberta: instalar a v1.1.0 das skills nos 4 destinos? Comando: `scripts/sync-skills.sh install prime --all --apply --replace` (idem session-handoff). Decisão do dono.
- Adiado: `mirror` ainda sobrescreve com backup sem modo prévia (fora do escopo desta tarefa).

## Próxima ação exata
Com aprovação do dono: instalar as skills v1.1.0 com `--apply --replace` e rodar `scripts/sync-skills.sh drift` (esperado 8/8 ok). Depois seguir `tasks/current.md`.

## Mapa de retomada
- `CHANGELOG.md` — o que mudou na 1.1.0
- `skills/prime/definition.md` e `skills/session-handoff/definition.md` — as duas skills
- `scripts/sync-skills.sh` e `tests/test-sync-skills.sh` — instalador e teste
- `context/decisions/2026-09-27-handoff-history.md` — por que latest.md é cópia
- `tasks/current.md` — tarefa em curso

## Checagem de compartilhamento
- Sem segredos, tokens, cookies, dados pessoais ou endpoints privados: sim. Nenhuma credencial citada.
