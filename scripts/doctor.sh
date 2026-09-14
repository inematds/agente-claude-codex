#!/usr/bin/env bash
# doctor.sh — diagnóstico do ambiente: o que está pronto pra usar o kit, o que falta e como resolver.
# Somente leitura. Uso: scripts/doctor.sh   (sai 0 se tudo essencial ok, 1 se falta algo essencial)
set -uo pipefail
ok(){ printf "  [ok]     %s\n" "$1"; }
warn(){ printf "  [aviso]  %s\n" "$1"; }
fail(){ printf "  [FALTA]  %s\n" "$1"; rc=1; }
rc=0

echo "== Sistema =="
ok "$(uname -s) $(uname -m), shell bash $BASH_VERSION"
for t in git python3; do command -v $t >/dev/null && ok "$t $($t --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9.]+' | head -1)" || fail "$t não encontrado (essencial pros scripts)"; done
command -v node >/dev/null && ok "node $(node --version)" || warn "node ausente: só o polyskill (passo 4) precisa dele"

echo "== Claude Code (fonte) =="
if command -v claude >/dev/null; then
  ok "claude $(claude --version 2>/dev/null | head -1)"
  [ -d "$HOME/.claude/skills" ] && ok "~/.claude/skills: $(ls -1 "$HOME/.claude/skills" | wc -l) skills" || warn "~/.claude/skills não existe (nada pra migrar ainda)"
  [ -f "$HOME/.claude/CLAUDE.md" ] && ok "~/.claude/CLAUDE.md existe ($(wc -l < "$HOME/.claude/CLAUDE.md") linhas)" || warn "sem CLAUDE.md global (adapt-instructions só roda por projeto)"
  [ -f "$HOME/.claude/settings.json" ] && ok "settings.json: $(python3 -c "import json;d=json.load(open('$HOME/.claude/settings.json'));print(sum(len(v) for v in d.get('hooks',{}).values()),'hooks,',len(d.get('enabledPlugins',{})),'plugins')" 2>/dev/null || echo 'não lido')"
else
  warn "claude não encontrado: audit e readback marcam Claude como não rodado. Instalar: https://docs.anthropic.com/claude-code"
fi

echo "== Codex CLI (destino) =="
if command -v codex >/dev/null; then
  ok "codex $(codex --version 2>/dev/null | head -1)"
  for d in "$HOME/.codex/skills" "$HOME/.agents/skills"; do [ -d "$d" ] && ok "$d: $(ls -1 "$d" | wc -l) skills" || warn "$d não existe (Codex cria ao instalar a 1ª skill)"; done
  if [ -f "$HOME/.codex/config.toml" ]; then
    sm=$(grep -oE '^sandbox_mode *= *"[^"]+"' "$HOME/.codex/config.toml" | grep -oE '"[^"]+"' | tr -d '"')
    ok "config.toml: sandbox_mode=${sm:-padrão}"
    if command -v bwrap >/dev/null && [ "$(sysctl -n kernel.apparmor_restrict_unprivileged_userns 2>/dev/null)" = "1" ] && [ "$sm" != "danger-full-access" ]; then
      warn "AppArmor restringe user namespaces: o sandbox bwrap do Codex pode falhar ('loopback: RTM_NEWADDR'). Em máquina pessoal confiável: sandbox_mode = \"danger-full-access\" no config.toml"
    fi
    grep -q '^\[mcp_servers' "$HOME/.codex/config.toml" && ok "MCP registrados no Codex" || warn "nenhum MCP no Codex: skills marcadas 'adaptador' só funcionam após 'codex mcp add'"
  else
    warn "~/.codex/config.toml ausente: rode 'codex' uma vez pra criar"
  fi
  codex --help 2>/dev/null | grep -qiE '^ *import' && ok "codex import disponível" || warn "Codex CLI sem comando import (o import 'um clique' é só no app desktop); use os scripts deste kit"
else
  warn "codex não encontrado: audit e readback marcam Codex como não rodado. Instalar: npm i -g @openai/codex"
fi

echo "== polyskill (passo 4) =="
command -v polyskill >/dev/null && ok "polyskill $(polyskill --version 2>/dev/null | tail -1)" || warn "polyskill ausente: npm i -g polyskill (só o sync-skills.sh precisa)"

echo "== Este kit =="
HERE="$(cd "$(dirname "$0")/.." && pwd)"
for f in scripts/audit.sh scripts/adapt-instructions.sh scripts/init-core.sh scripts/sync-skills.sh scripts/readback-test.sh template/AGENTS.md prompts/01-migrate-claude.md; do
  [ -f "$HERE/$f" ] && { [ -x "$HERE/$f" ] || [[ "$f" != scripts/* ]]; } && ok "$f" || fail "$f ausente ou sem permissão de execução (chmod +x scripts/*.sh)"
done
[ -w "$HERE" ] && ok "pasta gravável (relatorios/ será criada aqui)" || fail "sem permissão de escrita em $HERE"

echo
if [ $rc -eq 0 ]; then echo "Pronto. Próximo passo: scripts/audit.sh"; else echo "Faltam itens essenciais (marcados FALTA). Corrija e rode de novo."; fi
exit $rc
