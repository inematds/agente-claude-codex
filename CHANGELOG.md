# Changelog

Semver `vX.XX.YY`: patch incrementa YY; minor incrementa XX e carrega YY; só major zera.

## 1.10.3 — 2026-10-20

Motivo: trabalho fechado só sumia do índice; o snapshot ficava em history/, mas sem lista para achar depois (pedido do Nei, 20/10: "os fechados não poderiam ir para uma lista fechados, para pesquisa?").

- **`handoffs/fechados.md`**: `--fechado` grava ali uma linha por assunto (slug · snapshot do fechamento · data com ano · título do handoff), mais recente primeiro. Reabrir (gravar com o mesmo slug) tira de lá. `--fechados` lista. Fora do `latest.md`, que continua leve; o /prime só consulta quando o usuário pergunta por trabalho antigo.
- **`--recuperar-fechados`**: preenche a lista com os fechados de antes, pelos commits `handoff: <slug> (fechado)`; pula os reabertos e não duplica.
- **`--arrumar`**: sem snapshot novo, recupera os fechados, move os parados e regrava o índice, com commit só desses arquivos. Para aplicar a 1.9.3/1.10.3 em projetos já existentes de uma vez.
- Testes 36 → 41.

## 1.9.3 — 2026-10-20

Motivo: com vários terminais no mesmo projeto, o `latest.md` é o único arquivo que todos regravam. Sem trava, duas gravações ao mesmo tempo perdiam linha do índice (reproduzido: 8 gravações simultâneas → "leitura de volta não bate"). E o índice só encolhia com `--fechado`, que quase ninguém usa: o wifi tinha 42 assuntos "abertos", 11 sem handoff havia mais de 3 dias (pedido do Nei, 20/10, a partir de comentário no Skool).

- **handoff-grava.py — trava**: `flock` exclusivo na pasta `handoffs/history/` da leitura do índice até o commit (espera até 60 s; sem arquivo extra no repo). O hash dos arquivos (parte lenta) fica fora da trava.
- **handoff-grava.py — parados**: assunto sem handoff há mais de 3 dias sai dos abertos para o bloco `<!-- handoff-parados:inicio/fim -->` (teto de 50, os mais recentes). Gravar com o mesmo slug volta para os abertos; `--fechado` tira de lá também; `--parado-dias N` (ou `HANDOFF_PARADO_DIAS`; 0 desliga). Nenhum snapshot é apagado. `--listar` mostra os parados com a 4ª coluna `parado`.
- **session-handoff**: reusar o slug de linha `parado`. **prime**: não lista os parados, só a contagem.
- Hook-longrun (execucao-longa) não muda: ele lê só o bloco de abertos. Testes 31 → 36.

## 1.8.3 — 2026-10-18

Motivo: o briefing do `/prime` mostrava uma única "Regra principal"; com três restrições, duas ficavam de fora, e é a que fica de fora que o agente viola ao retomar. "Pela metade" e o porquê da próxima ação também não tinham lugar próprio (análise com o Nei, 18/10, a partir dos comentários do Skool).

- **session-handoff**: "Decisões e restrições" vira duas seções — **Decisões** (todas as que ainda valem) e **Não fazer (restrições e travas)**, todas, uma por item, com fonte. Seção nova **Pela metade** (começado, onde parou, o que falta). Próxima ação traz o porquê; pergunta-teste 5 vira "Qual é a próxima ação, por quê, e ela precisa de aprovação?". Regra 9 explica a seção Não fazer.
- **handoff-grava.py**: aviso (sem bloquear) quando falta a seção Não fazer. Testes 30 → 31.
- **prime**: passo 6b' (ler a seção Não fazer inteira e conferir a fonte de cada item) e três linhas no briefing — **Pela metade**, **Não fazer** (completa, mais as regras do AGENTS/CLAUDE que tocam a tarefa; handoff antigo cai em "Decisões e restrições") e **por quê** na próxima ação.
- `template/handoffs/latest.md` com as seções novas. Par com hook-longrun 1.8.4 (execucao-longa): mesma pergunta 5.
- Fora de escopo, de propósito: juiz automático da nota e cobertura por transcrição. Voltam se houver caso real de perda ou nota média < 4/5 após 2–3 semanas de medições.

## 1.7.3 — 2026-10-17

Motivo: o handoff do robot-v2 foi gravado no `~/projetos/wifi`, mas o trabalho acontece no `~/projetos/robot`; o `--conferir` olhava o repo errado. E um handoff saiu sem Perguntas-teste sem ninguém perceber (pedido do Nei, 17/10).

- **`handoff-grava.py --repo <caminho>`** (repetível, até 5): o bloco de estado ganha `### Repo do trabalho: <caminho>` com commit, branch, arquivos sujos e uma **impressão única de todos os sujos**. O `--conferir` confere esse repo também; com mais de 200 sujos, a impressão evita o alarme falso da lista cortada.
- **Avisos na gravação** (`aviso: …`, sem bloquear): corpo cita outro repo git sem `--repo`; falta a seção Perguntas-teste.
- **session-handoff**: quando usar `--repo` e o que fazer com os avisos (corrigir e gravar de novo).
- **prime (passo 6a')**: com `Repo do trabalho` no bloco, busca o estado real lá (`git -C <caminho> status/log`, leitura dos arquivos citados), só leitura; única exceção à recusa de caminho absoluto.
- Testes 25 → 30. Par com hook-longrun 1.8.3 (execucao-longa): `/clear` e `/prime` em linhas separadas nos avisos.

## 1.6.3 — 2026-10-17

Motivo: o `/prime` sem argumento abre o handoff mais recente do projeto; se outra sessão gravou depois, a sessão nova retomava o trabalho errado (pedido do Nei, 17/10).

- **handoff-grava.py imprime o comando de retomada** com o caminho exato do snapshot gravado: `/clear` + `/prime handoffs/history/<arquivo>.md` (no Codex, `/new`). Não imprime com `--fechado` nem `--indexar`. Testes 23 → 25.
- **session-handoff**: a resposta termina com esse comando pronto para copiar.
- **prime aceita argumento**: caminho do snapshot (usa exatamente esse, mesmo com outros mais novos; snapshot mais novo do mesmo assunto vira conflito) ou slug do assunto. Sem argumento, igual a antes.
- Instaladas em `~/.claude/skills` e `~/.agents/skills` (`--apply --replace`, backup feito). Cópias PT/EN no skillmanager3x. `dsh` e `v3` já estavam em drift antes desta versão e não foram tocados.

## 1.5.3 — 2026-10-17

- **handoff-grava.py: arquivo ilegível não derruba a gravação.** Sujo ou citado sem permissão de leitura vira `sha256:ilegivel` no bloco de estado, em vez de abortar o handoff (inclusive na cópia ociosa do hook, onde ninguém veria o erro). Teste novo (23).
- Limite conhecido: acima de 200 arquivos sujos a lista do bloco é cortada, e o `--conferir` acusa os excedentes como "mudou depois do handoff".

## 1.5.2 — 2026-10-17

Motivo: comentários do post "Não perca o contexto" no Skool (16/10): o handoff se autocertifica (quem escreve é o agente que pode ter se perdido), handoff velho é lido como atual, e falta um número para "quanto se perdeu" ao retomar.

- **session-handoff: bloco de estado gravado pelo script.** `handoff-grava.py` anexa ao snapshot (`<!-- handoff-estado:inicio/fim -->`) o commit (HEAD) e o sha256 (12 hex) dos arquivos citados em crase (até 20, só dentro da raiz, sem symlink) e dos sujos fora de `handoffs/` (até 200; arquivo > 100 MB: tamanho + começo + fim). Bloco escrito à mão no corpo é descartado. `--indexar` não altera snapshot existente.
- **`handoff-grava.py --conferir <snapshot>`** (só leitura): 0 = igual, 2 = divergente (arquivo citado/sujo que mudou ou sumiu, arquivo alterado depois do commit gravado, commit gravado que sumiu), 3 = snapshot sem bloco. Commit novo só com o mesmo conteúdo (ex.: o próprio commit do handoff, ou o trabalho sujo commitado depois) não é divergência.
- **session-handoff: evidência em todo `[confirmed]`** (`commit`, `teste:` ou `arquivo:`) e seção fixa **Perguntas-teste** (5 perguntas, resposta de uma linha, fonte num arquivo do projeto ou commit, nunca o próprio handoff).
- **prime**: passos 6a–6c (frescor pelo `--conferir`, ou `git diff`/`sha256sum` à mão; evidência dos `[confirmed]`; responder as perguntas-teste pelos arquivos e comparar) e três linhas novas no briefing: Frescor, Evidência, Perguntas-teste N/5. Divergência não vira ação sem o usuário confirmar.
- Testes: `tests/test_handoff_grava.py` 13 → 22 (pytest). Instaladas em `~/.claude/skills` e `~/.agents/skills` (`sync-skills.sh install --apply --replace`, backup feito); o Codex instalado estava sem o parágrafo da 1.5.1 e foi corrigido junto.

## 1.4.2 — 2026-10-15

- **session-handoff: handoff pedido pelo hook não encerra a sessão.** Regra nova em "Quando invocar": grave, avise em uma linha e continue a tarefa do usuário; sessão nova só ao fim da tarefa. Motivo: em 15/10 três sessões no wifi pararam no meio do pedido (vídeos 9:16, queimadas, refaz demos) dizendo "parei porque o contexto encheu" e o Nei teve de mandar "continue". Par com hook-longrun 1.2.1 (execucao-longa).

## 1.4.1 — 2026-10-15

- **session-handoff grava pelo script `scripts/handoff-grava.py`** (vai junto da skill nos 4 executores). Motivo: em 15/10 duas sessões no mesmo projeto (`~/projetos/wifi`) gravaram handoff em paralelo; a segunda sobrescreveu o `latest.md` e o plano da primeira sumiu do `/prime`; e um agente pôs no nome `T120000Z` num arquivo gravado às 07:45Z.
  - **Carimbo real**: o script usa o relógio da máquina; o nome é `<UTC>-<assunto>.md`, gravação exclusiva.
  - **`latest.md` = índice de trabalhos abertos** (uma linha por assunto, entre `<!-- handoff-indice:inicio/fim -->`) + cópia integral do snapshot mais novo, para quem lê o arquivo como documento. Assunto (slug) estável: a sessão reusa o do índice; `--fechado` tira do índice; `--indexar` registra snapshot já existente; `--listar` mostra. O índice também fica em `handoffs/indice.txt`: se uma sessão com a skill antiga sobrescrever o `latest.md`, ele não se perde.
  - **Commit do handoff**: em repositório git, um commit só com o snapshot e o `latest.md` (`git commit -- <caminhos>`; o que estiver staged por outra pessoa fica fora). Push continua manual. `--sem-commit` desliga.
  - Testes: `tests/test_handoff_grava.py` (13, pytest).
- **prime** aceita o formato índice, lista todos os trabalhos abertos no briefing (linha nova "Trabalhos abertos") e pergunta qual retomar quando o pedido não diz; aponta como conflito snapshot fora do índice e nome com hora posterior à gravação.
- Hook irmão: `inematds/execucao-longa` `hook-longrun` 1.2.0 lista os abertos na sessão limpa e avisa carimbo inventado.

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
