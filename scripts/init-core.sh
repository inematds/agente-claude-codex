#!/usr/bin/env bash
# init-core.sh — copia o núcleo portátil (template/) pra um projeto SEM sobrescrever nada que já exista.
# Uso: scripts/init-core.sh <pasta-do-projeto>
set -euo pipefail
DEST="${1:?pasta do projeto}"; SRC="$(cd "$(dirname "$0")/../template" && pwd)"
mkdir -p "$DEST"
( cd "$SRC" && find . -type f ) | while read -r f; do
  f="${f#./}"
  if [ -e "$DEST/$f" ]; then echo "[mantido]  $f"; else mkdir -p "$DEST/$(dirname "$f")"; cp "$SRC/$f" "$DEST/$f"; echo "[criado]   $f"; fi
done
echo "Agora preencha: $DEST/AGENTS.md, context/overview.md, tasks/current.md"
