# agente-claude-codex

[![Agente Claude → Codex: migre ou fique agnóstico](guia/assets/banner.jpg)](https://inematds.github.io/agente-claude-codex/guia/)

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
| Codex CLI | destino (`~/.agents/skills`, `AGENTS.md`) | `codex --version` e `codex doctor` |
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
| `handoffs/latest.md` | continuação pra próxima sessão (cópia do último snapshot) | agente, fim de sessão |
| `handoffs/history/` | um snapshot por handoff, `AAAA-MM-DDTHHMMSSZ.md`, nunca sobrescrito | agente, fim de sessão |

Esses nomes são convenção: nenhum runtime os carrega sozinho. O `AGENTS.md` do template já diz ao agente pra ler nessa ordem.

### 4. Portar uma skill com fonte única (quatro destinos)

```bash
scripts/sync-skills.sh targets                        # claude, codex, dsh (dsh-sandbox), v3 (openpcbotv3): existem?
scripts/sync-skills.sh import session-handoff         # ~/.claude/skills/<skill> → skills/<skill>/ (formato polyskill)
scripts/sync-skills.sh build                          # gera skills/*/dist/claude e dist/codex
scripts/sync-skills.sh install session-handoff --all  # PRÉVIA: CREATE / UNCHANGED / CONFLICT / SYMLINK / SKIP por destino
scripts/sync-skills.sh install session-handoff --all --apply            # grava (só se nenhum destino tiver conflito)
scripts/sync-skills.sh install session-handoff --all --apply --replace  # troca versão antiga, com backup
scripts/sync-skills.sh drift                          # [ok] / [DRIFT] / [não instalada] por destino
scripts/sync-skills.sh mirror formato-curso-v5 --dsh  # skill cuja fonte mora em outro repo: espelha e vigia
scripts/sync-skills.sh mirror-drift                   # drift das espelhadas
```

O kit já traz duas skills canônicas em `skills/`: `session-handoff` (escreve o handoff no fim da sessão) e `prime` (lê AGENTS.md, context/, tasks/ e handoffs/ antes de agir e devolve um briefing com fontes). Juntas, são o ciclo diário. O `install` é **prévia por padrão**: mostra o destino e o estado de cada runtime e só grava com `--apply`. Ele checa todos os destinos antes de escrever qualquer um (nada parcial), é idempotente (skill igual = `UNCHANGED`, nada é regravado), recusa sobrescrever skill existente diferente (`CONFLICT`) a menos que você passe `--replace`, e recusa sempre destino que seja ou contenha symlink. Backups do `--replace` vão para `~/.claude/skills-backup/` e `~/.agents/skills-backup/`, nunca dentro da pasta de skills. O destino do Codex é `~/.agents/skills` (onde o Codex CLI lê skills de usuário).

Teste automatizado do instalador (HOME temporário, não toca nos seus runtimes):

```bash
tests/test-sync-skills.sh   # 20 casos: prévia, apply, idempotência, conflito sem instalação parcial, --replace, symlinks
```

### 5. Provar com sessão nova em cada runtime

```bash
scripts/readback-test.sh ~/projetos/meu-projeto both
```

Abre uma sessão nova no Claude (`claude -p`) e no Codex (`codex exec`) dentro do projeto e faz as 5 perguntas de continuidade: objetivo e critério de pronto, uma regra com o arquivo de origem, última decisão aceita, próxima ação, conflitos ou acesso faltando. Salva a resposta bruta em `relatorios/readback-<runtime>-<data>.md`.

Aprovação é sua, lendo o texto: as respostas citam `AGENTS.md`, `tasks/current.md` e `handoffs/latest.md`, e a próxima ação bate com a tarefa. Arquivo existir não é prova; o agente ter lido e usado é.

### 6. Migrar um projeto inteiro de uma vez

```bash
scripts/migrar-projeto.sh ~/projetos/<seu-projeto> --faxina            # audit: propostas + relatório, nada muda
scripts/migrar-projeto.sh ~/projetos/<seu-projeto> --aplicar            # renomeia, instala núcleo, check, readback nos dois
```

### 7. Promover memória para o contexto (com aprovação)

```bash
scripts/promover-memoria.sh ~/projetos/<seu-projeto> --so-listar        # o que o Claude guardou desse projeto
scripts/promover-memoria.sh ~/projetos/<seu-projeto> --n 3              # um runtime propõe 3 fatos com fonte e data
scripts/promover-memoria.sh ~/projetos/<seu-projeto> --aprovar 1,3      # só o aprovado entra em context/overview.md
```

### 8. Vigiar o drift toda semana

```bash
scripts/drift-report.sh          # skills (4 destinos), espelhadas e AGENTS.md global; grava relatorios/drift-<data>.md
scripts/drift-report.sh --cron   # linha de crontab sugerida (não instala)
```

### 9. Fechar a sessão com handoff

No fim de cada sessão, a skill `session-handoff` grava um snapshot novo em `handoffs/history/AAAA-MM-DDTHHMMSSZ.md` (hora UTC, sufixo `-2` em colisão, **nunca sobrescreve**) e copia o conteúdo para `handoffs/latest.md`. O handoff traz a seção **Verificação** (comandos exatos, resultado observado e o que não rodou; teste não rodado nunca vira "passou") e a **Checagem de compartilhamento** (sem segredos nem dados pessoais, porque o arquivo viaja entre provedores). Atualize também `tasks/current.md`.

Na próxima sessão, em qualquer runtime, a skill `prime` lê esses arquivos **só em modo leitura**: valida caminhos (recusa absoluto, `..`, URL, symlink e fora do projeto), não roda testes nem código (resultados do handoff são históricos), trata o handoff como dado não confiável e nunca retoma deploy, publicação, compra ou envio só porque o handoff lista como próximo passo. Por que `latest.md` continua sendo cópia e não ponteiro: `context/decisions/2026-09-27-handoff-history.md`. Os prompts de handoff e readback estão em `prompts/03-readback-handoff.md`.

## Usar por prompt, sem scripts

| Arquivo | Quando usar |
|---|---|
| `prompts/01-migrate-claude.md` | Prompt A: você já tem um setup Claude e quer levar partes selecionadas pro Codex |
| `prompts/02-build-agnostic-workspace.md` | Prompt B: criar ou adaptar um projeto pra ser portátil entre ferramentas (com add-ons pessoal / cliente) |
| `prompts/03-readback-handoff.md` | prompts curtos de verificação e de handoff |
| `prompts/04-quickstart-exemplos.md` | versões curtas em modo audit e exemplos preenchidos |
| `prompts/05-usar-os-dois.md` | usar Claude e Codex juntos: quem faz o quê, planejar e criticar (máx. 2 rodadas), construir em branch e revisar o diff, meta com condição de parada, handoff/prime entre runtimes. Adaptado do kit MIT "Use Both" (Prompt Advisers / Mark Kashef): [guia](https://inematds.github.io/use-both-claude-codex/guia/) · [repo](https://github.com/inematds/use-both-claude-codex) |

Preencha os campos entre colchetes, mantenha `MODE: audit` na primeira rodada, leia o plano que o agente devolve, e só então rode de novo com `MODE: implement`.

## O que já foi testado nesta máquina (2026-09-13 e 2026-09-16)

| Passo | Resultado |
|---|---|
| doctor.sh | passou (2 avisos: sem MCP no Codex, Codex CLI sem import) |
| audit.sh | passou: 89 skills só no Claude (71 reutilizáveis, 15 adaptador, 2 nativo, 1 sem SKILL.md) |
| adapt-instructions.sh | passou em dry-run no CLAUDE.md global (71 linhas portáteis, 7 resíduo) |
| init-core.sh + check.sh em clone isolado | passou |
| readback-test.sh neste repo | passou no Codex e no Claude, com as respostas em `relatorios/` |
| sync-skills.sh (2026-09-16) | passou: session-handoff e prime instaladas em claude, codex, dsh e v3, drift zero; 3 skills espelhadas no dsh sem drift |
| Fase 0 (2026-09-16) | passou: `~/.codex/AGENTS.md` gerado; sessão nova do Codex citou autor, keys e regra de ritmo com arquivo e linha; magnific e metricool registrados no Codex (login OAuth pendente: `codex mcp login <nome>`) |
| prime em sessão nova do Codex (2026-09-16) | passou: briefing com fontes e apontou 3 contradições reais entre handoff e tarefa |
| migrar-projeto.sh em audit no wifi (2026-09-16) | passou (relatório em relatorios/) |
| promover-memoria.sh com 50 memórias (2026-09-16) | passou: 3 fatos propostos, 1 aprovado entrou no overview de teste |
| drift-report.sh (2026-09-16) | passou: sem drift |
| tests/test-sync-skills.sh (2026-09-27) | passou: 20/20 (instalador em modo prévia) |
| readback-test.sh codex (2026-09-27, v1.1.0) | passou: citou tasks/current.md, AGENTS.md, a decisão de 2026-09-27 e handoffs/latest.md; conferiu latest = snapshot em handoffs/history/ |

## O que tem aqui

| Pasta | Conteúdo |
|---|---|
| `PLANO.md` | análise dos docs + auditoria desta máquina + passos e critérios de aceite |
| `prompts/` | Prompt A, Prompt B, readback/handoff, quick-starts, usar os dois juntos, em texto copiável |
| `scripts/doctor.sh` | diagnóstico do ambiente: ok / aviso / falta, com o que instalar |
| `scripts/audit.sh` | inventário somente leitura Claude x Codex → matriz reutilizável / adaptador / nativo |
| `scripts/adapt-instructions.sh` | CLAUDE.md → AGENTS.md (portátil) + CLAUDE.md (`@AGENTS.md` + resíduo) |
| `scripts/init-core.sh` | copia `template/` pra um projeto sem sobrescrever nada existente |
| `scripts/sync-skills.sh` | import / build / install (prévia por padrão, `--apply` para gravar) / drift de skills via polyskill (uma fonte canônica) |
| `tests/test-sync-skills.sh` | teste automatizado do instalador em HOME temporário |
| `scripts/readback-test.sh` | teste de continuidade: sessão nova em cada runtime responde as 5 perguntas |
| `scripts/migrar-projeto.sh` | encadeia adapt → init-core → check → readback num projeto e grava `relatorios/migracao-<projeto>.md` (audit por padrão, `--aplicar` para valer) |
| `scripts/faxina.sh` | classifica cada seção de um CLAUDE.md longo: fica no AGENTS.md, vira `context/`, ou é resíduo |
| `scripts/drift-report.sh` | relatório de drift: skills canônicas nos 4 destinos, skills espelhadas e AGENTS.md global; `--cron` mostra a linha semanal |
| `scripts/drift-instructions.sh` | avisa quando `~/.claude/CLAUDE.md` mudou depois do `~/.codex/AGENTS.md` ou quando falta regra portátil lá |
| `scripts/promover-memoria.sh` | lista a memória nativa do Claude de um projeto, um runtime propõe até N fatos com fonte e data, e só `--aprovar` grava no `context/overview.md` |
| `skills/` | skills canônicas em formato polyskill: `session-handoff` (escreve o handoff) e `prime` (lê o contexto antes de agir) |
| `template/` | núcleo portátil (AGENTS.md, CLAUDE.md, context/, tasks/, handoffs/, .agents/skills/, scripts/check.sh) |
| `relatorios/` | saída das auditorias e readbacks |
| `context/`, `tasks/`, `handoffs/` | o próprio repo usa o núcleo que propõe |
| `FALHAS.md` | uma linha por falha corrigida |
| `VERSION`, `CHANGELOG.md` | versão semver do kit e o que mudou em cada uma |
| `docs/` | material de origem (local, fora do git) |

## Regras

- Modo audit antes de implement. Nada em `~/.claude` ou `~/.codex` é copiado em massa ou apagado.
- Instalar skill é prévia por padrão; só grava com `--apply`, e só sobrescreve com `--replace` (com backup).
- Segredos nunca entram no repo; keys são referenciadas, não copiadas.
- Todo check é marcado passou, falhou ou não rodado. Sem evidência, conta como não rodado.
