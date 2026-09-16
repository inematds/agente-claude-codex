#!/usr/bin/env bash
# drift-report.sh — relatório semanal de drift: skills canônicas (4 destinos), skills espelhadas (dsh/v3)
# e instruções globais (CLAUDE.md vs AGENTS.md). Grava relatorios/drift-<data>.md e sai 1 se houver DRIFT.
# Uso: scripts/drift-report.sh            # roda e grava
#      scripts/drift-report.sh --cron     # imprime a linha de crontab sugerida (não instala nada)
set -uo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
if [ "${1:-}" = "--cron" ]; then echo "0 8 * * 1 cd $HERE && scripts/drift-report.sh >/dev/null 2>&1   # segunda 08:00; ver relatorios/drift-*.md"; exit 0; fi
mkdir -p relatorios; R="relatorios/drift-$(date +%Y-%m-%d).md"; rc=0
{
echo "# Drift — $(date '+%Y-%m-%d %H:%M')"; echo
echo "## Skills canônicas (skills/ → claude, codex, dsh, v3)"; echo '```'
scripts/sync-skills.sh drift || rc=1
echo '```'; echo
echo "## Skills espelhadas (fonte em ~/.claude/skills → dsh, v3)"; echo '```'
scripts/sync-skills.sh mirror-drift || rc=1
echo '```'; echo
echo "## Instruções globais (~/.claude/CLAUDE.md → ~/.codex/AGENTS.md)"; echo '```'
scripts/drift-instructions.sh || rc=1
echo '```'; echo
echo "Resultado: $([ $rc = 0 ] && echo 'sem drift' || echo 'DRIFT encontrado — rode build/install ou mirror, e regenere o AGENTS.md global')"
} | tee "$R"
echo "Relatório: $R"; exit $rc
