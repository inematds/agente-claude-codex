# AGENTS.md — instruções portáteis do projeto

> Ordem de leitura para qualquer agente (Claude Code, Codex, Gemini, OpenCode, Claude.ai e ChatGPT por conector GitHub): 1) este arquivo, 2) `context/overview.md`, 3) `context/current-state.md`, 4) `tasks/current.md`, 5) `handoffs/latest.md`. Estes nomes são convenção deste repo, não são carregados automaticamente: leia-os.

## Regras do projeto
- (regras estáveis, portáteis, sem nada específico de um runtime)

## Mesmo contexto em várias plataformas
- Este repo é a fonte da verdade. Antes de ler: pegue a main mais nova. Depois de escrever: commit + push na main.
- Instruções para colar no Claude.ai, ChatGPT e Codex na nuvem: `plataformas/instrucoes-projeto.md` (fonte única do texto).
- Como ligar cada plataforma e testar: `plataformas/README.md`.
- O que a IA aprender vira regra aqui, skill em `.agents/skills/` ou fato em `context/`, nunca só memória do app.

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
| Handoff | handoffs/history/<UTC>.md + cópia em handoffs/latest.md | agente | fim de sessão |
