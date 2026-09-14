#!/usr/bin/env bash
# adapt-instructions.sh — gera o par de adaptadores de instrução para um projeto:
#   AGENTS.md  = regras portáteis (lidas por Codex, Gemini, OpenCode...)
#   CLAUDE.md  = "@AGENTS.md" + resíduo específico do Claude Code
# Uso: scripts/adapt-instructions.sh <pasta-do-projeto> [--dry-run]
# Atenção: renomeia toda menção 'CLAUDE.md' → 'AGENTS.md' na parte portátil, inclusive referências a CLAUDE.md de OUTROS projetos; revisar.
# Não sobrescreve arquivos existentes: grava *.proposto.md ao lado para revisão.
set -euo pipefail
ROOT="${1:?pasta do projeto}"; DRY="${2:-}"
SRC="$ROOT/CLAUDE.md"
[ -f "$SRC" ] || { echo "sem CLAUDE.md em $ROOT — nada a adaptar"; exit 0; }

# Linhas exclusivas do Claude Code (ficam no resíduo do CLAUDE.md):
CLAUDE_ONLY='AskUserQuestion|superpowers|context-mode|fable-mindset|claude-mem|ultrareview|/code-review|Artifact|advisor|plugin|hook'

PORT="$ROOT/AGENTS.proposto.md"; RES="$ROOT/CLAUDE.proposto.md"
{
  echo "# AGENTS.md — instruções portáteis do projeto"
  echo
  echo "> Ordem de leitura para qualquer agente: 1) este arquivo, 2) context/overview.md, 3) context/current-state.md, 4) tasks/current.md, 5) handoffs/latest.md. Estes nomes são convenção: nada é carregado automaticamente fora do AGENTS.md/CLAUDE.md."
  echo
  grep -vE "$CLAUDE_ONLY" "$SRC" | sed 's/CLAUDE\.md/AGENTS.md/g'
} > "$PORT"
{
  echo "@AGENTS.md"
  echo
  echo "# Específico do Claude Code (não portátil)"
  echo
  grep -E "$CLAUDE_ONLY" "$SRC" || echo "_(nada específico encontrado)_"
} > "$RES"

echo "Propostos (revisar e renomear manualmente):"
echo "  $PORT  ($(wc -l < "$PORT") linhas)"
echo "  $RES   ($(wc -l < "$RES") linhas)"
[ "$DRY" = "--dry-run" ] && { rm -f "$PORT" "$RES"; echo "(dry-run: arquivos removidos)"; }
exit 0
