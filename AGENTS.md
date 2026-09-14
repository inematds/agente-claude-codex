# AGENTS.md — agente-claude-codex

> Ordem de leitura: 1) este arquivo, 2) `PLANO.md`, 3) `context/overview.md`, 4) `tasks/current.md`, 5) `handoffs/latest.md`. Nada disso é carregado automaticamente: leia.

## Regras
- Este repo opera em **modo audit por padrão**: scripts leem `~/.claude` e `~/.codex`, nunca apagam nem copiam em massa. Instalar skill (`sync-skills.sh install`) faz backup ao lado antes.
- Segredos nunca entram no repo. Keys vivem em `~/projetos/openpcbotv2/.env` ou `~/projetos/wifi/.env`; referencie, não copie.
- Publicar = commit + push no git. Autor `inematds <inematds@gmail.com>`. `docs/` fica fora do git (material de terceiros) até decisão do dono.
- Versionamento semver `vX.XX.YY`: patch incrementa YY; minor incrementa XX e carrega YY; só major zera.
- Relatórios de evidência vão em `relatorios/`; todo check é marcado passou / falhou / não rodado.

## Skills e scripts
- Skills canônicas importadas ficam em `skills/<nome>/` (formato polyskill); cópias por runtime em `skills/<nome>/dist/`.
- Comandos em `scripts/` (ver README).

## Donos da informação
| Tipo | Arquivo | Atualiza |
|---|---|---|
| Plano e critérios | PLANO.md | humano aceita, agente propõe |
| Visão geral | context/overview.md | agente, ao promover fato verificado |
| Decisões | context/decisions/ | humano |
| Tarefa atual | tasks/current.md | humano define, agente marca |
| Handoff | handoffs/latest.md | agente, fim de sessão |
