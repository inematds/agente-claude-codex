# agente-claude-codex

Kit pra migrar um setup Claude Code pro Codex **ou** deixar o trabalho independente de modelo: separar o "cérebro" (contexto, decisões, tarefas, handoffs, skills) do executor (Claude, Codex, Gemini, local).

Baseado na newsletter "Como migrar do Claude para o Codex — ou ficar independente de modelo" e na prompt library "Model-agnostic workspaces" (07 SEP 2026). Leia `PLANO.md` pra entender a análise e o piloto recomendado.

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/agente-claude-codex/guia/**

## Não tem interface gráfica

É um kit de linha de comando (bash) mais arquivos Markdown. Três formas de usar:

1. **Scripts** (`scripts/`): auditar, adaptar, instalar núcleo, portar skill, provar. É o caminho principal, descrito abaixo.
2. **Prompts** (`prompts/`): os mega-prompts A e B em texto copiável, pra colar num agente (Claude Code, Codex, outro) e fazer a migração conversando. Comece sempre com `MODE: audit`.
3. **Template** (`template/`): o núcleo portátil pra copiar em qualquer projeto, mesmo sem rodar os scripts.

## Pré-requisitos

| Ferramenta | Pra quê | Como conferir |
|---|---|---|
| Claude Code | fonte da migração (`~/.claude/skills`, `CLAUDE.md`) | `claude --version` |
| Codex CLI | destino (`~/.codex/skills`, `~/.agents/skills`, `AGENTS.md`) | `codex --version` e `codex doctor` |
| polyskill | portar skill com fonte única pros dois runtimes | `npm i -g polyskill` |
| bash, git, python3 | os scripts usam só isso | já vem no Linux/macOS |

Sem Claude ou Codex instalado, o passo correspondente é marcado como **não rodado**, não falha.

## Passo a passo

### 0. Clonar e diagnosticar o ambiente

```bash
git clone https://github.com/inematds/agente-claude-codex
cd agente-claude-codex
scripts/doctor.sh
```

Responde "meu ambiente está pronto?" antes de qualquer coisa. Confere git, python3, node, Claude Code (skills, CLAUDE.md, hooks), Codex CLI (skills, config, sandbox, MCP), polyskill e os arquivos do próprio kit. Cada item sai como `[ok]`, `[aviso]` (funciona, com limitação) ou `[FALTA]` (essencial, com o comando pra resolver). Somente leitura; sai com código 1 se faltar algo essencial.

### 1. Auditar o que existe (somente leitura)

```bash
scripts/audit.sh
```

Produz `relatorios/auditoria-<data>.md` com: versões, quantidade de skills / comandos / subagentes / hooks / MCP em cada runtime, e a matriz de cada skill que existe só no Claude classificada como **reutilizável** (Markdown puro), **adaptador** (depende de MCP ou plugin do Claude), **nativo** (depende de hook) ou **não resolvido**. Nada em `~/.claude` ou `~/.codex` é alterado.

### 2. Separar as instruções portáteis do resíduo Claude

```bash
scripts/adapt-instructions.sh ~/projetos/meu-projeto
```

Lê o `CLAUDE.md` do projeto e grava dois arquivos ao lado, sem sobrescrever nada:

- `AGENTS.proposto.md`: regras portáteis, com ordem de leitura no topo (Codex, Gemini e OpenCode leem `AGENTS.md`).
- `CLAUDE.proposto.md`: `@AGENTS.md` mais só o que é específico do Claude Code (plugins, hooks, AskUserQuestion).

Revise, renomeie pra `AGENTS.md` e `CLAUDE.md`. Atenção: menções a `CLAUDE.md` de outros projetos também são renomeadas; confira.

### 3. Instalar o núcleo portátil no projeto

```bash
scripts/init-core.sh ~/projetos/meu-projeto
```

Copia `template/` sem sobrescrever o que já existe e lista o que criou e o que manteve. Depois preencha:

| Arquivo | O que vai | Quem atualiza |
|---|---|---|
| `AGENTS.md` | regras estáveis + ordem de leitura | humano |
| `context/overview.md` | o que é, fatos verificados (com fonte e data), preferências, hipóteses | agente, ao promover fato |
| `context/current-state.md` | o que funciona e o que está pendente | agente, fim de sessão |
| `context/sources.md` | de onde vem cada informação e regra de refresh | humano |
| `context/decisions/` | uma decisão aceita por arquivo | humano |
| `tasks/current.md` | objetivo, dono, critério de pronto, próxima ação | humano define, agente marca |
| `handoffs/latest.md` | continuação pra próxima sessão | agente, fim de sessão |

Esses nomes são convenção: nenhum runtime os carrega sozinho. O `AGENTS.md` do template já diz ao agente pra ler nessa ordem.

### 4. Portar uma skill com fonte única

```bash
scripts/sync-skills.sh import session-handoff   # ~/.claude/skills/session-handoff → skills/session-handoff/ (formato polyskill)
scripts/sync-skills.sh build                    # gera skills/*/dist/claude e dist/codex
scripts/sync-skills.sh install session-handoff --both   # copia pros runtimes (backup ao lado se já existia)
scripts/sync-skills.sh drift                    # [ok] ou [DRIFT] por runtime
```

Piloto recomendado: `session-handoff`, porque é o mecanismo do ciclo diário (sessão → handoff → nova sessão lê o handoff). Use `--codex` ou `--claude` no install pra um runtime só.

### 5. Provar com sessão nova em cada runtime

```bash
scripts/readback-test.sh ~/projetos/meu-projeto both
```

Abre uma sessão nova no Claude (`claude -p`) e no Codex (`codex exec`) dentro do projeto e faz as 5 perguntas de continuidade: objetivo e critério de pronto, uma regra com o arquivo de origem, última decisão aceita, próxima ação, conflitos ou acesso faltando. Salva a resposta bruta em `relatorios/readback-<runtime>-<data>.md`.

Aprovação é sua, lendo o texto: as respostas citam `AGENTS.md`, `tasks/current.md` e `handoffs/latest.md`, e a próxima ação bate com a tarefa. Arquivo existir não é prova; o agente ter lido e usado é.

### 6. Fechar a sessão com handoff

No fim de cada sessão, atualize `handoffs/latest.md` e `tasks/current.md`. Na próxima sessão, em qualquer runtime, o agente começa lendo esses dois. Os prompts de handoff e readback estão em `prompts/03-readback-handoff.md`.

## Usar por prompt, sem scripts

| Arquivo | Quando usar |
|---|---|
| `prompts/01-migrate-claude.md` | Prompt A: você já tem um setup Claude e quer levar partes selecionadas pro Codex |
| `prompts/02-build-agnostic-workspace.md` | Prompt B: criar ou adaptar um projeto pra ser portátil entre ferramentas (com add-ons pessoal / cliente) |
| `prompts/03-readback-handoff.md` | prompts curtos de verificação e de handoff |
| `prompts/04-quickstart-exemplos.md` | versões curtas em modo audit e exemplos preenchidos |

Preencha os campos entre colchetes, mantenha `MODE: audit` na primeira rodada, leia o plano que o agente devolve, e só então rode de novo com `MODE: implement`.

## O que já foi testado nesta máquina (2026-09-13)

| Passo | Resultado |
|---|---|
| doctor.sh | passou (2 avisos: sem MCP no Codex, Codex CLI sem import) |
| audit.sh | passou: 89 skills só no Claude (71 reutilizáveis, 15 adaptador, 2 nativo, 1 sem SKILL.md) |
| adapt-instructions.sh | passou em dry-run no CLAUDE.md global (71 linhas portáteis, 7 resíduo) |
| init-core.sh + check.sh em clone isolado | passou |
| readback-test.sh neste repo | passou no Codex e no Claude, com as respostas em `relatorios/` |
| sync-skills.sh | **não rodado** ainda |

## O que tem aqui

| Pasta | Conteúdo |
|---|---|
| `PLANO.md` | análise dos docs + auditoria desta máquina + passos e critérios de aceite |
| `prompts/` | Prompt A, Prompt B, readback/handoff, quick-starts, em texto copiável |
| `scripts/doctor.sh` | diagnóstico do ambiente: ok / aviso / falta, com o que instalar |
| `scripts/audit.sh` | inventário somente leitura Claude x Codex → matriz reutilizável / adaptador / nativo |
| `scripts/adapt-instructions.sh` | CLAUDE.md → AGENTS.md (portátil) + CLAUDE.md (`@AGENTS.md` + resíduo) |
| `scripts/init-core.sh` | copia `template/` pra um projeto sem sobrescrever nada existente |
| `scripts/sync-skills.sh` | import / build / install / drift de skills via polyskill (uma fonte canônica) |
| `scripts/readback-test.sh` | teste de continuidade: sessão nova em cada runtime responde as 5 perguntas |
| `template/` | núcleo portátil (AGENTS.md, CLAUDE.md, context/, tasks/, handoffs/, .agents/skills/, scripts/check.sh) |
| `relatorios/` | saída das auditorias e readbacks |
| `context/`, `tasks/`, `handoffs/` | o próprio repo usa o núcleo que propõe |
| `FALHAS.md` | uma linha por falha corrigida |
| `docs/` | material de origem (local, fora do git) |

## Regras

- Modo audit antes de implement. Nada em `~/.claude` ou `~/.codex` é copiado em massa ou apagado.
- Instalar skill faz backup ao lado antes de sobrescrever.
- Segredos nunca entram no repo; keys são referenciadas, não copiadas.
- Todo check é marcado passou, falhou ou não rodado. Sem evidência, conta como não rodado.
