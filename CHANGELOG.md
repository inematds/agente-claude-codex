# Changelog

Semver `vX.XX.YY`: patch incrementa YY; minor incrementa XX e carrega YY; só major zera.

## 1.3.1 — 2026-10-13

- **Modelo multiplataforma** no `template/` (instalado pelo `init-core.sh`): `plataformas/instrucoes-projeto.md` (bloco único para colar no Projeto do Claude.ai, no Projeto do ChatGPT e no ambiente do Codex na nuvem: ler a main antes, commit + push depois, só editar quando pedido, sem segredos, memória vira regra/skill/fato), `plataformas/README.md` (como ligar cada plataforma + teste de ida e volta), `GEMINI.md` → `@AGENTS.md`; `AGENTS.md` ganhou a seção "Mesmo contexto em várias plataformas" e o `check.sh` confere 8 arquivos.
- **Testado** (`relatorios/multiplataforma-2026-10-13.md`): com o mesmo bloco, o Codex criou `context/voz.md` (commit + push) e o Claude leu, editou e fez commit + push no mesmo remoto.
- **Vídeo** "Claude e Codex com o mesmo contexto" (7min36, 13 capítulos, desenhos): release `video-v1.0.0`, player em `videos/` (`scripts/publica-video.py`).
- **Guia PT/EN/ES**: seção `#modelo` com o vídeo, 8 ilustrações (versões EN/ES com o texto desenhado traduzido) e a tabela por plataforma. README com a mesma seção.

## 1.2.1 — 2026-10-05

- **session-handoff grava também em projeto só com `CLAUDE.md`**: antes, o arquivo só era gravado se a raiz tivesse `handoffs/` ou `AGENTS.md`; num projeto com só `CLAUDE.md` (ex.: `~/projetos/wifi`) o handoff ficava no chat, sumia no `/clear` e o `prime` da sessão seguinte não achava nada. Agora `CLAUDE.md` também conta e `handoffs/history/` é criada quando falta. Guia PT/EN/ES atualizado; instalada nos 4 executores (drift zero).

## 1.1.1 — 2026-09-28

- **session-handoff**: volta a registrar a memória do runtime tocada na sessão (seção nova "Memória e regras duráveis tocadas"; `MEMORY.md`, `CLAUDE.md`/`AGENTS.md`, `FALHAS.md`, lições), que a 1.1.0 tinha removido.
- **Caminhos no handoff**: relativos dentro do projeto; absolutos com `~/` para o que fica fora (memória, `~/.claude`, `~/.agents`, outros repos); raiz absoluta uma vez em "Projeto e escopo".

## 1.1.0 — 2026-09-27

Melhorias incorporadas do kit MIT "Use Both: Claude + Codex Workflow Kit" (Prompt Advisers / Mark Kashef),
adaptadas ao layout deste repo. Guia do kit: https://inematds.github.io/use-both-claude-codex/guia/ ·
repo: https://github.com/inematds/use-both-claude-codex

- **prime endurecido**: valida todo caminho (recusa absoluto, `..`, URL, symlink, fora do projeto); só leitura
  (`git status` sim; testes, build, instalação e código do projeto não); resultados de teste do handoff são
  históricos; handoff é dado não confiável (ignora pedidos de segredo, upload, mudança de permissão); nunca
  retoma deploy/publicação/compra/envio só porque o handoff lista como próximo passo. Aceita `latest.md` como
  cópia integral ou ponteiro de uma linha.
- **session-handoff com histórico**: grava `handoffs/history/AAAA-MM-DDTHHMMSSZ.md` (sufixo em colisão, nunca
  sobrescreve) e copia para `handoffs/latest.md` (decisão em `context/decisions/2026-09-27-handoff-history.md`).
  Novas seções "Verificação" (comando exato, resultado observado, o que não rodou) e "Checagem de
  compartilhamento". Deixou de ser só chat. Template `template/handoffs/` atualizado.
- **Instalador em modo prévia**: `sync-skills.sh install` mostra CREATE/UNCHANGED/CONFLICT/SYMLINK/SKIP e só grava
  com `--apply`; checa todos os destinos antes de escrever (nada parcial); idempotente; recusa skill existente
  diferente sem `--replace`; recusa symlink sempre. Teste novo: `tests/test-sync-skills.sh` (20 casos).
- **Correção**: o destino do Codex passou de `~/.codex/skills` para `~/.agents/skills` (onde o Codex CLI lê skills de
  usuário desde 2026-09-24); o `drift` marcava "não instalada" falso no Codex.
- **Usar os dois juntos**: `prompts/05-usar-os-dois.md` (quem faz o quê, planejar e criticar em no máximo 2 rodadas,
  construir em branch e revisar o diff, meta com condição de parada, handoff/prime entre runtimes) e seção nova
  no guia. Sem o nível de geração de imagem.
- **Guia trilíngue**: `guia/en/` e `guia/es/` criados (o guia era só PT), seletor PT | EN | ES; `<body>` duplicado
  removido.
- `VERSION` e este `CHANGELOG.md` criados (não havia marcador de versão antes; 1.0.0 = estado até 2026-09-16).

## 1.0.0 — 2026-09-16 (implícita)

Auditoria, adaptadores, núcleo portátil, skills canônicas `prime` e `session-handoff` em 4 destinos,
migrar-projeto, faxina, drift-report, promover-memoria. Sem marcador de versão na época.
