#!/usr/bin/env bash
# readback-test.sh — teste de continuidade: abre sessão NOVA em cada runtime e pergunta
# objetivo, regra+fonte, última decisão, próxima ação, conflitos. Não edita nada.
# Uso: scripts/readback-test.sh <pasta-do-projeto> [claude|codex|both]   (default: both)
# Obs.: não força sandbox no Codex; usa o sandbox_mode do ~/.codex/config.toml (neste host o bwrap falha por AppArmor).
# Saída: relatorios/readback-<runtime>-<data>.md com o texto bruto; o veredito (passou/falhou)
# é seu — o script só marca "não rodado" quando o runtime não existe.
set -euo pipefail
ROOT="$(cd "${1:?pasta do projeto}" && pwd)"; RT="${2:-both}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PROMPT="$(sed -n '/^```text/,/^```/p' "$HERE/prompts/03-readback-handoff.md" | sed '1d;$d' | sed -n '1,/^$/p')"
mkdir -p "$HERE/relatorios"; D=$(date +%Y-%m-%d)

run_claude() {
  command -v claude >/dev/null || { echo "claude: não rodado (não instalado)"; return; }
  echo "→ claude (sessão nova em $ROOT)"
  ( cd "$ROOT" && claude -p "$PROMPT" ) > "$HERE/relatorios/readback-claude-$D.md" 2>&1 || true
  echo "  salvo: relatorios/readback-claude-$D.md ($(wc -l < "$HERE/relatorios/readback-claude-$D.md") linhas)"
}
run_codex() {
  command -v codex >/dev/null || { echo "codex: não rodado (não instalado)"; return; }
  echo "→ codex exec (sessão nova em $ROOT)"
  ( cd "$ROOT" && codex exec --skip-git-repo-check "$PROMPT" ) > "$HERE/relatorios/readback-codex-$D.md" 2>&1 || true
  echo "  salvo: relatorios/readback-codex-$D.md ($(wc -l < "$HERE/relatorios/readback-codex-$D.md") linhas)"
}
case "$RT" in claude) run_claude ;; codex) run_codex ;; both) run_claude; run_codex ;; *) echo "runtime inválido"; exit 1 ;; esac
echo
echo "Critério de aprovação (marque manualmente): as 5 respostas citam arquivos do projeto (AGENTS.md, context/, tasks/current.md, handoffs/latest.md) e a 'próxima ação' bate com tasks/current.md."
