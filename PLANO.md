# Plano — Claude Code → Codex, ou ficar agnóstico

Data: 2026-09-13. Modo: **audit** (nada em `~/.claude` ou `~/.codex` foi alterado).
Fontes: `docs/migrar-claude-para-codex-model-agnostic.md`, `docs/prompt-vs-texto-model-agnostic.md`, `docs/mega-prompts.pdf` (Prompt A, Prompt B, readback/handoff), auditoria real em `relatorios/auditoria-2026-09-13.md`.

## 1. O que os documentos dizem, em uma linha cada

- **Texto 1 (filosofia):** não migre o cérebro do Claude pro Codex; separe o cérebro do modelo. Só `CLAUDE.md`/`AGENTS.md` são presos ao provedor, o resto é Markdown portátil. Fluxo diário: sessão → `/handoff` → Markdown → `/prime` → sessão nova.
- **Texto 2 (do conceito ao procedimento):** a ideia vira uma árvore concreta (`AGENTS.md`, `context/`, `tasks/current.md`, `handoffs/latest.md`, `.agents/skills/`, `scripts/`), com dono por tipo de informação, skill canônica + adaptadores, e teste de continuidade obrigatório.
- **PDF (prompts executáveis):** Prompt A migra um setup Claude existente; Prompt B constrói o workspace portátil. Ambos começam em `MODE: audit` (analisar → planejar → simular) e só depois `implement`. O próprio PDF admite: nenhuma migração real foi testada pelos autores.

## 2. O que a auditoria desta máquina mostrou

| Item | Situação |
|---|---|
| Claude Code | 2.1.270, 116 skills, 0 slash commands, 7 subagentes, 4 runbooks, 2 hooks SessionStart, MCP global: magnific, metricool |
| Codex CLI | 0.154.0, 27 skills em `~/.codex/skills` (≈ `~/.agents/skills`, 29), 0 MCP, hooks PostToolUse+Stop (impeccable) |
| polyskill | 0.1.0 instalado (import/build/install cross-runtime) |
| Import nativo | **Não existe no Codex CLI** (`codex --help` não tem `import`). O "Nível 1 um clique" do texto é o app desktop. O `npx migrate to codex` do texto é hipotético. |
| Gap de skills | 89 só no Claude: 73 reutilizáveis (Markdown puro), 17 precisam adaptador (MCP/plugin do Claude), 4 nativas (hook) — heurística por grep, revisar |
| Subagentes | Sem equivalente 1:1 no Codex: classificar como nativo, virar skill de "papel" |
| CLAUDE.md global | 71 linhas portáteis, 7 específicas do Claude (dry-run de `scripts/adapt-instructions.sh`) |

## 3. Os três níveis, traduzidos pra esta máquina

| Nível | Texto propõe | Aqui |
|---|---|---|
| 1 — um clique | Importar no app Codex | Só no app desktop, não no CLI. Não depende deste repo. |
| 2 — um comando | `npx migrate to codex` | **Este repo é esse comando.** `scripts/audit.sh` → `scripts/adapt-instructions.sh` → `scripts/sync-skills.sh` → `scripts/readback-test.sh`. |
| 3 — pessoal (camada durável) | `context/`, playbooks, handoffs | `template/` = núcleo portátil copiável pra qualquer projeto. Runbooks de `~/.claude/runbooks` viram `context/` do projeto que os usa. |

## 4. Piloto recomendado

**Skill piloto: `session-handoff` + um `prime` (leitura de `handoffs/latest.md`).** É o mecanismo em que todo o texto se apoia e hoje só existe no Claude. Tarefa representativa: abrir sessão nova no Codex, rodar prime, responder as 5 perguntas do readback citando arquivos.

**Projeto piloto:** este próprio repo (já tem o núcleo) ou um projeto real que você escolher. Sugestão: um projeto INEMA pequeno com `CLAUDE.md` próprio.

## 5. Passos (ordem, cada um reversível)

1. **Auditar** — `scripts/audit.sh` (feito, relatório em `relatorios/`).
2. **Instruções** — `scripts/adapt-instructions.sh <projeto>` gera `AGENTS.proposto.md` + `CLAUDE.proposto.md`; revisar, renomear. Claude passa a ler `@AGENTS.md`.
3. **Núcleo portátil** — copiar `template/` pro projeto, preencher `context/overview.md`, `tasks/current.md`.
4. **Skills** — `scripts/sync-skills.sh import session-handoff` → `build` → `install session-handoff --both` → `drift`.
5. **Hooks** — `fable-mindset` (SessionStart) não tem equivalente no Codex; o playbook vai pro `AGENTS.md` do projeto como texto. `impeccable` já roda nos dois.
6. **MCP** — magnific e metricool: registrar no Codex com `codex mcp add` só se um projeto precisar, referenciando as keys de `~/projetos/openpcbotv2/.env` (nunca copiar valor).
7. **Provar** — `scripts/readback-test.sh <projeto> both`; marcar passou / falhou / não rodado com o texto salvo.
8. **Handoff** — atualizar `handoffs/latest.md` e `tasks/current.md`.

## 6. Critérios de aceite

- Sessão nova no Codex e no Claude respondem as 5 perguntas do readback citando `AGENTS.md`, `tasks/current.md`, `handoffs/latest.md`.
- `scripts/sync-skills.sh drift` sem DRIFT pra skill piloto.
- Projeto copiado sozinho pra pasta limpa passa `scripts/check.sh`.
- Setup Claude continua funcionando (nada em `~/.claude` removido).

## 7. Riscos e limites

- Classificação de skills é heurística. 17 skills dependem de MCP/plugins (heygen, magnific, printing-press): no Codex só funcionam após registrar o MCP correspondente.
- Subagentes (`~/.claude/agents`) e plugins (superpowers, context-mode, claude-mem) não migram. Ficam como resíduo Claude.
- `docs/` tem material de terceiros (post traduzido + prompt library datada de 07 SEP 2026). Está no `.gitignore` até decisão: repo privado, ou manter só as reescritas próprias.
- Nenhum teste de readback foi rodado até a seção abaixo ser preenchida.

## 8. Evidência de execução

Ver `handoffs/latest.md` (atualizado a cada rodada).
