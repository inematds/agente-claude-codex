#!/usr/bin/env bash
# drift-instructions.sh — detecta quando ~/.claude/CLAUDE.md (fonte) mudou depois que ~/.codex/AGENTS.md foi gerado,
# e mostra quais regras portáteis do CLAUDE.md não estão no AGENTS.md. Só lê. Sai 1 se houver drift.
# Regenerar: scripts/adapt-instructions.sh ~/.claude → revisar → gravar ~/.codex/AGENTS.md (ver handoffs/latest.md).
set -uo pipefail
SRC="$HOME/.claude/CLAUDE.md"; DST="$HOME/.codex/AGENTS.md"
[ -f "$SRC" ] || { echo "sem $SRC"; exit 0; }
[ -f "$DST" ] || { echo "[DRIFT] $DST não existe — rode adapt-instructions.sh ~/.claude"; exit 1; }
rc=0
if [ "$SRC" -nt "$DST" ]; then echo "[DRIFT] CLAUDE.md ($(date -r "$SRC" +%F' '%H:%M)) é mais novo que AGENTS.md ($(date -r "$DST" +%F' '%H:%M))"; rc=1; else echo "[ok] AGENTS.md gerado depois da última edição do CLAUDE.md"; fi
CLAUDE_ONLY='AskUserQuestion|superpowers|context-mode|fable-mindset|claude-mem|ultrareview|/code-review|Artifact|advisor|plugin|hook'
miss=0
while IFS= read -r l; do
  [[ "$l" =~ ^-\ \*\* ]] || continue                      # só bullets de regra ("- **...")
  key=$(echo "$l" | grep -oE '^\- \*\*[^*]{6,60}' | sed 's/^- \*\*//')
  [ -z "$key" ] && continue
  echo "$l" | grep -qE "$CLAUDE_ONLY" && continue          # resíduo Claude, não deveria estar no AGENTS
  grep -qF "$key" "$DST" || { echo "[falta no AGENTS.md] $key"; miss=$((miss+1)); }
done < "$SRC"
[ "$miss" -gt 0 ] && rc=1 || echo "[ok] todas as regras portáteis do CLAUDE.md constam no AGENTS.md"
exit $rc
