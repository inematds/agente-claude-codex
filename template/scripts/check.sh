#!/usr/bin/env bash
# check.sh — verificação mínima do núcleo portátil: arquivos obrigatórios existem e não estão vazios.
set -e; cd "$(dirname "$0")/.."
for f in AGENTS.md README.md context/overview.md context/current-state.md context/sources.md tasks/current.md handoffs/latest.md; do
  [ -s "$f" ] && echo "[ok] $f" || { echo "[FALTA] $f"; rc=1; }
done; exit ${rc:-0}
