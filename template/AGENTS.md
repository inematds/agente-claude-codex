# AGENTS.md — instruções portáteis do projeto

> Ordem de leitura para qualquer agente (Claude Code, Codex, Gemini, OpenCode): 1) este arquivo, 2) `context/overview.md`, 3) `context/current-state.md`, 4) `tasks/current.md`, 5) `handoffs/latest.md`. Estes nomes são convenção deste repo, não são carregados automaticamente: leia-os.

## Regras do projeto
- (regras estáveis, portáteis, sem nada específico de um runtime)

## Skills e scripts
- Skills canônicas em `.agents/skills/<nome>/SKILL.md` (Codex lê daqui; o Claude recebe cópia gerada).
- Comandos reproduzíveis em `scripts/`.

## Donos da informação
| Tipo | Arquivo | Quem atualiza | Quando |
|---|---|---|---|
| Instruções estáveis | AGENTS.md | humano | ao mudar regra |
| Visão geral / fatos | context/overview.md, context/sources.md | humano + agente | ao promover fato verificado |
| Estado atual | context/current-state.md | agente | fim de sessão |
| Decisões aceitas | context/decisions/AAAA-MM-DD-*.md | humano aceita | ao decidir |
| Tarefa atual | tasks/current.md | humano define, agente marca | por tarefa |
| Handoff | handoffs/latest.md | agente | fim de sessão |
