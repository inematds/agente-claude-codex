#!/usr/bin/env bash
# audit.sh — inventário SOMENTE LEITURA do setup Claude Code x Codex desta máquina.
# Gera uma matriz origem → destino (reutilizável / adaptador / nativo / não resolvido) em Markdown.
# Não altera nada em ~/.claude nem ~/.codex. Nunca imprime valores de chaves.
set -euo pipefail

OUT="${1:-relatorios/auditoria-$(date +%Y-%m-%d).md}"
mkdir -p "$(dirname "$OUT")"
CL="$HOME/.claude"; CX="$HOME/.codex"; AG="$HOME/.agents"

count() { [ -d "$1" ] && ls -1 "$1" 2>/dev/null | wc -l || echo 0; }
listdir() { [ -d "$1" ] && ls -1 "$1" 2>/dev/null | sort || true; }

{
echo "# Auditoria Claude Code → Codex — $(date '+%Y-%m-%d %H:%M')"
echo
echo "Modo: audit (somente leitura). Host: $(uname -s) $(uname -r)."
echo
echo "## 1. Versões e raízes"
echo
echo "| Item | Valor |"
echo "|---|---|"
echo "| claude | $(claude --version 2>/dev/null | head -1 || echo 'não instalado') |"
echo "| codex | $(codex --version 2>/dev/null | head -1 || echo 'não instalado') |"
echo "| polyskill | $(polyskill --version 2>/dev/null | tail -1 || echo 'não instalado') |"
echo "| ~/.claude/skills | $(count "$CL/skills") skills |"
echo "| ~/.claude/commands | $(count "$CL/commands") comandos |"
echo "| ~/.claude/agents | $(count "$CL/agents") subagentes |"
echo "| ~/.claude/runbooks | $(count "$CL/runbooks") runbooks |"
echo "| ~/.codex/skills | $(count "$CX/skills") skills |"
echo "| ~/.agents/skills | $(count "$AG/skills") skills |"
echo "| Codex import nativo (CLI) | $(codex --help 2>/dev/null | grep -qi '^ *import' && echo 'sim' || echo 'não existe no CLI — só no app') |"
echo
echo "## 2. Skills: gap Claude → Codex"
echo
comm -23 <(listdir "$CL/skills") <(listdir "$CX/skills") > /tmp/_gap.txt || true
comm -12 <(listdir "$CL/skills") <(listdir "$CX/skills") > /tmp/_both.txt || true
echo "- Já nos dois: $(wc -l < /tmp/_both.txt)"
echo "- Só no Claude: $(wc -l < /tmp/_gap.txt)"
echo
echo "### 2.1 Classificação automática das que faltam no Codex"
echo
echo "Heurística: skill que cita ferramenta MCP (\`mcp__\`), \`AskUserQuestion\`, \`Agent(\`, hooks ou plugins do Claude é marcada como *adaptador* ou *nativo*; o resto é *reutilizável* (Markdown puro)."
echo
echo "| Skill | Classificação | Motivo |"
echo "|---|---|---|"
while read -r s; do
  [ -z "$s" ] && continue
  f="$CL/skills/$s/SKILL.md"
  if [ ! -f "$f" ]; then echo "| $s | não resolvido | sem SKILL.md |"; continue; fi
  if grep -qE 'mcp__|claude-in-chrome|magnific|heygen-mcp' "$f"; then echo "| $s | adaptador | depende de MCP/conector do Claude |";
  elif grep -qE 'AskUserQuestion|subagent_type|Agent\(|superpowers:|claude-mem' "$f"; then echo "| $s | adaptador | usa ferramenta/plugin exclusivo do Claude Code |";
  elif grep -qE 'hooks?\.(json|mjs|sh)|SessionStart|PreToolUse' "$f"; then echo "| $s | nativo | depende de hook |";
  else echo "| $s | reutilizável | Markdown + scripts comuns |"; fi
done < /tmp/_gap.txt
echo
echo "## 3. Comandos, subagentes, hooks, plugins"
echo
echo "| Ativo Claude | Qtd | Destino Codex | Classificação |"
echo "|---|---|---|---|"
echo "| slash commands (~/.claude/commands) | $(count "$CL/commands") | skills | reutilizável (vazio hoje) |"
echo "| subagentes (~/.claude/agents) | $(count "$CL/agents") | sem equivalente 1:1 | nativo — virar skill de 'papel' ou prompt |"
echo "| hooks (settings.json) | $(python3 -c "import json;print(sum(len(v) for v in json.load(open('$CL/settings.json')).get('hooks',{}).values()))" 2>/dev/null || echo '?') | ~/.codex/hooks.json | adaptador — eventos diferem (Codex: PostToolUse, Stop) |"
echo "| plugins (enabledPlugins) | $(python3 -c "import json;print(len(json.load(open('$CL/settings.json')).get('enabledPlugins',{})))" 2>/dev/null || echo '?') | codex plugin | nativo |"
echo "| runbooks (~/.claude/runbooks) | $(count "$CL/runbooks") | context/ do projeto | reutilizável |"
echo "| CLAUDE.md global | 1 | AGENTS.md (+ resíduo Claude) | adaptador — ver scripts/adapt-instructions.sh |"
echo "| memória (~/.claude/projects/*/memory) | $(find "$CL/projects" -maxdepth 2 -type d -name memory 2>/dev/null | wc -l) projetos | context/ + handoffs/ | promoção manual, nunca cópia em massa |"
echo
echo "## 4. Hooks do Codex hoje"
echo
echo '```json'
[ -f "$CX/hooks.json" ] && python3 -c "import json;d=json.load(open('$CX/hooks.json'));print(json.dumps({k:[h.get('matcher','*') for h in v] for k,v in d.get('hooks',{}).items()},indent=1))" || echo "{}"
echo '```'
echo
echo "## 5. MCP (só nomes, sem valores)"
echo
echo "- Claude (~/.claude.json global): $(python3 -c "import json;print(', '.join(json.load(open('$HOME/.claude.json')).get('mcpServers',{}).keys()) or 'nenhum global')" 2>/dev/null || echo 'não lido')"
echo "- Codex (config.toml [mcp_servers]): $(grep -oE '^\[mcp_servers\.[^]]+\]' "$CX/config.toml" 2>/dev/null | sed 's/\[mcp_servers\.//;s/\]//' | tr '\n' ' ' || true)$(grep -q '^\[mcp_servers' "$CX/config.toml" 2>/dev/null || echo 'nenhum')"
echo
echo "## 6. Não rodado / limitações"
echo
echo "- Nenhum teste de comportamento foi executado por este script. Use \`scripts/readback-test.sh\` para evidência real."
echo "- Classificação de skills é heurística por grep; revisar antes de migrar."
} > "$OUT"

echo "Relatório: $OUT"
grep -cE '\| reutilizável' "$OUT" | xargs -I{} echo "  reutilizável: {}"
grep -cE '\| adaptador' "$OUT" | xargs -I{} echo "  adaptador:    {}"
grep -cE '\| nativo' "$OUT" | xargs -I{} echo "  nativo:       {}"
