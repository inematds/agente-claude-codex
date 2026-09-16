#!/usr/bin/env bash
# sync-skills.sh — uma fonte canônica de skill (formato polyskill) → N executores, com checagem de drift.
# Destinos: claude (~/.claude/skills), codex (~/.codex/skills + espelho ~/.agents/skills),
#           dsh (~/projetos/dsh-skills, montado no container do dsh-sandbox), v3 (~/projetos/openpcbotv3/skills).
# dsh e v3 aceitam o mesmo SKILL.md do Claude, então recebem a saída dist/claude.
# Uso:
#   scripts/sync-skills.sh import <skill> [<skill>...]      # ~/.claude/skills/<skill> → skills/<skill>/ (canônico)
#   scripts/sync-skills.sh build                             # skills/*/ → skills/*/dist/{claude,codex}
#   scripts/sync-skills.sh install <skill> [--all|--claude|--codex|--dsh|--v3 ...]   (default: --claude --codex)
#   scripts/sync-skills.sh drift [<skill>]                   # [ok] / [DRIFT] / [não instalada] por destino
#   scripts/sync-skills.sh targets                           # mostra os caminhos de cada destino e se existem
# Requer: polyskill (npm i -g polyskill). Backups vão para ~/.<rt>/skills-backup/ (nunca dentro de skills/).
set -euo pipefail
cd "$(dirname "$0")/.."
DSH_DIR="${DSH_SKILLS_DIR:-$HOME/projetos/dsh-skills}"
V3_DIR="${V3_SKILLS_DIR:-$HOME/projetos/openpcbotv3/skills}"
mkdir -p skills

dest_of() { # $1=destino $2=skill → caminho instalado
  case "$1" in
    claude) echo "$HOME/.claude/skills/$2" ;;
    codex)  echo "$HOME/.codex/skills/$2" ;;
    dsh)    echo "$DSH_DIR/$2" ;;
    v3)     echo "$V3_DIR/$2" ;;
  esac
}
src_of() { # $1=destino $2=skill → pasta em dist/
  case "$1" in codex) echo "skills/$2/dist/codex/$2" ;; *) echo "skills/$2/dist/claude/$2" ;; esac
}
backup_dir() { case "$1" in claude) echo "$HOME/.claude/skills-backup" ;; codex) echo "$HOME/.codex/skills-backup" ;; dsh) echo "$DSH_DIR/../dsh-skills-backup" ;; v3) echo "$V3_DIR/../skills-backup" ;; esac; }

cmd="${1:-}"; shift || true
case "$cmd" in
  import)
    command -v polyskill >/dev/null || { echo "polyskill não instalado: npm i -g polyskill"; exit 1; }
    for s in "$@"; do
      src="$HOME/.claude/skills/$s"
      [ -d "$src" ] || { echo "skip $s: não existe em ~/.claude/skills"; continue; }
      ( cd skills && polyskill import "$src" --from claude >/dev/null ) && echo "importada: skills/$s"
    done ;;
  build)
    command -v polyskill >/dev/null || { echo "polyskill não instalado: npm i -g polyskill"; exit 1; }
    for d in skills/*/; do ( cd "$d" && polyskill build ${FORCE:+--force} >/dev/null ) && echo "build: $d"; done ;;
  install)
    s="${1:?skill}"; shift || true
    tg=("$@"); [ ${#tg[@]} -eq 0 ] && tg=(--claude --codex)
    [[ " ${tg[*]} " == *" --all "* ]] && tg=(--claude --codex --dsh --v3)
    for t in "${tg[@]}"; do
      rt="${t#--}"; out="$(src_of "$rt" "$s")"; dest="$(dest_of "$rt" "$s")"
      [ -d "$out" ] || { echo "rode build antes: $out"; exit 1; }
      [ -d "$(dirname "$dest")" ] || { echo "[skip] destino $rt não existe: $(dirname "$dest")"; continue; }
      if [ -e "$dest" ]; then b="$(backup_dir "$rt")"; mkdir -p "$b"; cp -a "$dest" "$b/$s.bak-$(date +%s)"; rm -rf "$dest"; fi
      cp -a "$out" "$dest"; echo "instalada: $dest"
      [ "$rt" = codex ] && [ -d "$HOME/.agents/skills" ] && { rm -rf "$HOME/.agents/skills/$s"; cp -a "$out" "$HOME/.agents/skills/$s"; echo "espelhada: ~/.agents/skills/$s"; }
      true
    done ;;
  drift)
    rc=0; only="${1:-}"
    for d in skills/*/; do
      s=$(basename "$d"); [ -n "$only" ] && [ "$s" != "$only" ] && continue
      for rt in claude codex dsh v3; do
        out="$(src_of "$rt" "$s")"; tgt="$(dest_of "$rt" "$s")"
        [ -d "$out" ] || { echo "[sem build]      $s → $rt"; continue; }
        [ -d "$tgt" ] || { echo "[não instalada]  $s → $rt"; continue; }
        if diff -rq "$out" "$tgt" >/dev/null; then echo "[ok]             $s → $rt"; else echo "[DRIFT]          $s → $rt"; rc=1; fi
      done
    done; exit $rc ;;
  mirror)
    # Para skills cuja fonte canônica mora em OUTRO repo (ex.: formato-curso-* em formato-curso-inema, ligadas por
    # symlink em ~/.claude/skills): espelha ~/.claude/skills/<s> (dereferenciado) em dsh/v3, e o drift compara com a fonte.
    s="${1:?skill}"; shift || true; tg=("$@"); [ ${#tg[@]} -eq 0 ] && tg=(--dsh)
    src="$(readlink -f "$HOME/.claude/skills/$s")"; [ -d "$src" ] || { echo "fonte não existe: ~/.claude/skills/$s"; exit 1; }
    for t in "${tg[@]}"; do rt="${t#--}"; case "$rt" in dsh|v3) ;; *) echo "mirror só aceita --dsh/--v3"; exit 2;; esac
      dest="$(dest_of "$rt" "$s")"; [ -d "$(dirname "$dest")" ] || { echo "[skip] destino $rt não existe"; continue; }
      if [ -e "$dest" ] && diff -rq "$src" "$dest" >/dev/null; then echo "[ok] $s → $rt já igual à fonte"; continue; fi
      if [ -e "$dest" ]; then b="$(backup_dir "$rt")"; mkdir -p "$b"; cp -a "$dest" "$b/$s.bak-$(date +%s)"; rm -rf "$dest"; fi
      cp -a "$src/." "$dest/" 2>/dev/null || { mkdir -p "$dest"; cp -a "$src/." "$dest/"; }; echo "espelhada: $dest (fonte: $src)"
    done ;;
  mirror-drift)
    # drift das skills espelhadas: compara cada skill em dsh/v3 que exista em ~/.claude/skills com a fonte
    rc=0
    for rt in dsh v3; do d="$(dirname "$(dest_of "$rt" x)")"; [ -d "$d" ] || continue
      for p in "$d"/*/; do s=$(basename "$p"); [[ "$s" == _* ]] && continue; src="$(readlink -f "$HOME/.claude/skills/$s" 2>/dev/null)"
        [ -d "$src" ] || { echo "[só em $rt]      $s"; continue; }
        if diff -rq "$src" "$p" >/dev/null; then echo "[ok]             $s → $rt"; else echo "[DRIFT]          $s → $rt (fonte ~/.claude/skills/$s)"; rc=1; fi
      done
    done; exit $rc ;;
  targets)
    for rt in claude codex dsh v3; do d="$(dirname "$(dest_of "$rt" x)")"; [ -d "$d" ] && echo "[ok]    $rt → $d ($(ls -1 "$d" | wc -l) skills)" || echo "[falta] $rt → $d"; done ;;
  *) sed -n '2,12p' "$0"; exit 1 ;;
esac
