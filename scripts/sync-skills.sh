#!/usr/bin/env bash
# sync-skills.sh — leva skills selecionadas do Claude Code para o formato portátil (polyskill)
# e gera as cópias para cada runtime, com checagem de drift.
# Uso:
#   scripts/sync-skills.sh import <skill> [<skill>...]   # ~/.claude/skills/<skill> → skills/<skill>/ (canônico)
#   scripts/sync-skills.sh build                          # skills/*/ → dist/{claude,codex}/
#   scripts/sync-skills.sh drift                          # compara dist/ com ~/.claude/skills e ~/.codex/skills
#   scripts/sync-skills.sh install <skill> [--codex|--claude|--both]
# Requer: polyskill (npm i -g polyskill). Nunca copia ~/.claude ou ~/.codex em massa.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v polyskill >/dev/null || { echo "polyskill não instalado: npm i -g polyskill"; exit 1; }
mkdir -p skills dist
cmd="${1:-}"; shift || true
case "$cmd" in
  import)
    for s in "$@"; do
      src="$HOME/.claude/skills/$s"
      [ -d "$src" ] || { echo "skip $s: não existe em ~/.claude/skills"; continue; }
      ( cd skills && polyskill import "$src" --from claude ) && echo "importada: skills/$s"
    done ;;
  build)
    for d in skills/*/; do ( cd "$d" && polyskill build ${FORCE:+--force} ) && echo "build: $d"; done ;;
  drift)
    rc=0
    for d in skills/*/; do
      s=$(basename "$d")
      for rt in claude codex; do
        out="$d/dist/$rt/$s"; tgt="$HOME/.$rt/skills/$s"
        [ -d "$out" ] && [ -d "$tgt" ] || { echo "[não instalada] $s → $rt"; continue; }
        if diff -rq "$out" "$tgt" >/dev/null; then echo "[ok] $s → $rt"; else echo "[DRIFT] $s → $rt"; rc=1; fi
      done
    done; exit $rc ;;
  install)
    s="${1:?skill}"; tgt="${2:---both}"
    for rt in claude codex; do
      case "$tgt" in --both) ;; --$rt) ;; *) continue ;; esac
      out="skills/$s/dist/$rt/$s"; [ -d "$out" ] || { echo "rode build antes: $out"; exit 1; }
      dest="$HOME/.$rt/skills/$s"
      [ -e "$dest" ] && cp -a "$dest" "$HOME/.$rt/skills/.$s.bak-$(date +%s)"
      mkdir -p "$(dirname "$dest")"; cp -a "$out" "$dest"; echo "instalada: $dest (backup ao lado se já existia)"
      # Codex também descobre em ~/.agents/skills
      [ "$rt" = codex ] && [ -d "$HOME/.agents/skills" ] && cp -a "$out" "$HOME/.agents/skills/$s" && echo "espelhada: ~/.agents/skills/$s"
    done ;;
  *) sed -n '2,9p' "$0"; exit 1 ;;
esac
