# Overview — agente-claude-codex
- ID: overview | Escopo: este repo | Fonte: docs/ (3 textos + PDF) e auditoria local | Data: 2026-09-13 | Status: aceito | Revisar: ao mudar versão do Codex ou do Claude Code

## O que é
Kit de migração/agnosticismo: scripts de auditoria e adaptação + template de núcleo portátil + prompts A/B do PDF.

## Fatos verificados (2026-09-13)
- Codex CLI 0.154.0 não tem comando `import`; o import "um clique" é do app desktop.
- Claude Code 2.1.270 com 116 skills; Codex com 27 (`~/.codex/skills` ≈ `~/.agents/skills`).
- polyskill 0.1.0 instalado globalmente.
- MCP no Claude: magnific, metricool. No Codex: nenhum.
- Hooks Codex: PostToolUse e Stop (impeccable). Claude: SessionStart (context-mode, fable-mindset).

## Preferências do dono
- Ver AGENTS.md (audit primeiro, sem cópia em massa, segredos fora).

## Hipóteses (não verificadas)
- A classificação heurística de 73 skills como "reutilizável" está correta na maioria; precisa amostragem.
