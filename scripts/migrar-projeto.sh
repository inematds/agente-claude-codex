#!/usr/bin/env bash
# migrar-projeto.sh — encadeia a migração de UM projeto: adapt-instructions → init-core → check → readback,
# e grava um relatório com o que passou / falhou / não rodou.
# Uso: scripts/migrar-projeto.sh <pasta-do-projeto> [--aplicar] [--readback claude|codex|both|none] [--faxina]
#   sem --aplicar: modo audit — gera os *.proposto.md e o relatório, não renomeia nada, não instala núcleo.
#   --aplicar    : renomeia AGENTS.proposto.md → AGENTS.md e CLAUDE.proposto.md → CLAUDE.md (backup dos originais
#                  em <projeto>/.migracao-backup/), roda init-core.sh e check.sh.
#   --readback   : roda readback-test.sh no fim (default: none em audit, both com --aplicar).
#   --faxina     : roda faxina.sh (relatório do que no CLAUDE.md deveria virar context/).
set -uo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
P="${1:?pasta do projeto}"; shift || true
[ -d "$P" ] || { echo "pasta não existe: $P"; exit 2; }
P="$(cd "$P" && pwd)"; NAME="$(basename "$P")"
APLICAR=0; RB=""; FAX=0
while [ $# -gt 0 ]; do case "$1" in --aplicar) APLICAR=1;; --readback) RB="$2"; shift;; --faxina) FAX=1;; *) echo "arg desconhecido: $1"; exit 2;; esac; shift; done
[ -z "$RB" ] && { [ $APLICAR = 1 ] && RB=both || RB=none; }
mkdir -p relatorios; R="relatorios/migracao-$NAME-$(date +%Y-%m-%d).md"
res=(); add(){ res+=("| $1 | $2 | $3 |"); }

echo "== migrar-projeto: $NAME (modo: $([ $APLICAR = 1 ] && echo implement || echo audit)) =="
# 1. estado git
if git -C "$P" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  dirty=$(git -C "$P" status --short | wc -l); add "git" "$([ "$dirty" = 0 ] && echo passou || echo aviso)" "working tree com $dirty arquivos sujos; branch $(git -C "$P" branch --show-current)"
else add "git" "aviso" "não é repo git"; fi
# 2. instruções
if [ -f "$P/CLAUDE.md" ]; then
  L=$(wc -l < "$P/CLAUDE.md"); scripts/adapt-instructions.sh "$P" >/dev/null 2>&1 && add "adapt-instructions" "passou" "CLAUDE.md com $L linhas → AGENTS.proposto.md ($(wc -l < "$P/AGENTS.proposto.md") linhas) + CLAUDE.proposto.md ($(wc -l < "$P/CLAUDE.proposto.md") linhas)" || add "adapt-instructions" "falhou" "ver saída"
  [ "$L" -gt 300 ] && add "faxina" "aviso" "CLAUDE.md tem $L linhas (>300): rode --faxina antes de aplicar"
elif [ -f "$P/AGENTS.md" ]; then add "adapt-instructions" "não rodado" "já tem AGENTS.md e não tem CLAUDE.md"
else add "adapt-instructions" "não rodado" "sem CLAUDE.md nem AGENTS.md"; fi
[ $FAX = 1 ] && [ -f "$P/CLAUDE.md" ] && { scripts/faxina.sh "$P" > "relatorios/faxina-$NAME-$(date +%Y-%m-%d).md" 2>&1 && add "faxina.sh" "passou" "relatorios/faxina-$NAME-$(date +%Y-%m-%d).md"; }
# 3. aplicar
if [ $APLICAR = 1 ]; then
  if [ -f "$P/AGENTS.proposto.md" ]; then
    mkdir -p "$P/.migracao-backup"; for f in AGENTS.md CLAUDE.md; do [ -f "$P/$f" ] && cp -a "$P/$f" "$P/.migracao-backup/$f.$(date +%s)"; done
    mv "$P/AGENTS.proposto.md" "$P/AGENTS.md"; mv "$P/CLAUDE.proposto.md" "$P/CLAUDE.md"; add "aplicar instruções" "passou" "AGENTS.md + CLAUDE.md gravados; originais em .migracao-backup/"
    grep -q '^@AGENTS.md' "$P/CLAUDE.md" || add "aplicar instruções" "aviso" "CLAUDE.md não começa com @AGENTS.md"
  fi
  out=$(scripts/init-core.sh "$P" 2>&1); add "init-core" "passou" "$(echo "$out" | grep -c '\[criado\]') criados, $(echo "$out" | grep -c '\[mantido\]') mantidos"
  if [ -x "$P/scripts/check.sh" ]; then bash "$P/scripts/check.sh" >/dev/null 2>&1 && add "check.sh" "passou" "arquivos obrigatórios presentes" || add "check.sh" "falhou" "faltam arquivos (preencher context/, tasks/, handoffs/)"; fi
else add "aplicar / init-core / check" "não rodado" "modo audit; use --aplicar"; fi
# 4. readback
if [ "$RB" != none ]; then
  scripts/readback-test.sh "$P" "$RB" >/dev/null 2>&1
  for rt in claude codex; do f="relatorios/readback-$rt-$(date +%Y-%m-%d).md"; case "$RB" in both|$rt) ;; *) continue;; esac
    if [ -s "$f" ]; then hits=$(grep -cE 'AGENTS\.md|tasks/current\.md|handoffs/latest\.md|CLAUDE\.md' "$f"); add "readback $rt" "$([ "$hits" -ge 2 ] && echo passou || echo falhou)" "$hits citações de arquivos do núcleo em $f (aprovação final é humana)"
    else add "readback $rt" "não rodado" "sem saída (runtime ausente ou erro)"; fi; done
else add "readback" "não rodado" "--readback none"; fi
{ echo "# Migração — $NAME — $(date '+%Y-%m-%d %H:%M')"; echo; echo "Modo: $([ $APLICAR = 1 ] && echo implement || echo audit). Projeto: \`$P\`"; echo; echo "| Passo | Resultado | Detalhe |"; echo "|---|---|---|"; printf '%s\n' "${res[@]}"; echo; echo "Próximo: $([ $APLICAR = 1 ] && echo 'preencher context/overview.md e tasks/current.md, rodar readback de novo, escrever handoffs/latest.md' || echo 'revisar os *.proposto.md e rodar com --aplicar')"; } > "$R"
printf '%s\n' "${res[@]}" | sed 's/^| //;s/ |$//'; echo "Relatório: $R"
