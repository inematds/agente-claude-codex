# Auditoria Claude Code → Codex — 2026-09-13 22:43

Modo: audit (somente leitura). Host: Linux 6.14.0-1015-nvidia.

## 1. Versões e raízes

| Item | Valor |
|---|---|
| claude | 2.1.270 (Claude Code) |
| codex | codex-cli 0.154.0 |
| polyskill | 0.1.0 |
| ~/.claude/skills | 116 skills |
| ~/.claude/commands | 0 comandos |
| ~/.claude/agents | 7 subagentes |
| ~/.claude/runbooks | 4 runbooks |
| ~/.codex/skills | 27 skills |
| ~/.agents/skills | 29 skills |
| Codex import nativo (CLI) | não existe no CLI — só no app |

## 2. Skills: gap Claude → Codex

- Já nos dois: 27
- Só no Claude: 89

### 2.1 Classificação automática das que faltam no Codex

Heurística: skill que cita ferramenta MCP (`mcp__`), `AskUserQuestion`, `Agent(`, hooks ou plugins do Claude é marcada como *adaptador* ou *nativo*; o resto é *reutilizável* (Markdown puro).

| Skill | Classificação | Motivo |
|---|---|---|
| 3d-animation-creator | reutilizável | Markdown + scripts comuns |
| agent-browser | reutilizável | Markdown + scripts comuns |
| agent-reach | reutilizável | Markdown + scripts comuns |
| algorithmic-art | reutilizável | Markdown + scripts comuns |
| animation-designer | reutilizável | Markdown + scripts comuns |
| anuncio-edita | reutilizável | Markdown + scripts comuns |
| audit-ablacao | reutilizável | Markdown + scripts comuns |
| auditor-video-ia | reutilizável | Markdown + scripts comuns |
| avaliar-erros-de-fluxos | reutilizável | Markdown + scripts comuns |
| avatar-heygen-nei | adaptador | depende de MCP/conector do Claude |
| beautiful-mermaid | reutilizável | Markdown + scripts comuns |
| brand-guidelines | reutilizável | Markdown + scripts comuns |
| capa-inema | reutilizável | Markdown + scripts comuns |
| clima | reutilizável | Markdown + scripts comuns |
| comfy | reutilizável | Markdown + scripts comuns |
| comfy-build | reutilizável | Markdown + scripts comuns |
| comfy-debug | reutilizável | Markdown + scripts comuns |
| comfy-deploy | reutilizável | Markdown + scripts comuns |
| comfy-director | reutilizável | Markdown + scripts comuns |
| comfy-relay | adaptador | usa ferramenta/plugin exclusivo do Claude Code |
| course-completer | reutilizável | Markdown + scripts comuns |
| design-dna | reutilizável | Markdown + scripts comuns |
| diretor-animacao | reutilizável | Markdown + scripts comuns |
| doc-coauthoring | reutilizável | Markdown + scripts comuns |
| dublagem-compasso | reutilizável | Markdown + scripts comuns |
| espiona-ads | adaptador | depende de MCP/conector do Claude |
| excalidraw-diagram-generator | reutilizável | Markdown + scripts comuns |
| fable-mindset | nativo | depende de hook |
| filme | reutilizável | Markdown + scripts comuns |
| forja-reel | reutilizável | Markdown + scripts comuns |
| formato-curso-v4 | reutilizável | Markdown + scripts comuns |
| formato-curso-v5 | reutilizável | Markdown + scripts comuns |
| fs-seis-chapeus | reutilizável | Markdown + scripts comuns |
| generate | reutilizável | Markdown + scripts comuns |
| grill-me | reutilizável | Markdown + scripts comuns |
| heygen-cli | adaptador | depende de MCP/conector do Claude |
| heygen-mcp | adaptador | depende de MCP/conector do Claude |
| heygen-video-nei | reutilizável | Markdown + scripts comuns |
| imagens-agnes | reutilizável | Markdown + scripts comuns |
| impeccable | reutilizável | Markdown + scripts comuns |
| inemaref-folder | reutilizável | Markdown + scripts comuns |
| inemaref-motioncomic | reutilizável | Markdown + scripts comuns |
| inemaref-quadrinho | reutilizável | Markdown + scripts comuns |
| inemaref-referencias | não resolvido | sem SKILL.md |
| inemaref-serie | reutilizável | Markdown + scripts comuns |
| kling-3-0 | reutilizável | Markdown + scripts comuns |
| maestro-roteador | reutilizável | Markdown + scripts comuns |
| making-of-simulacao | reutilizável | Markdown + scripts comuns |
| making-of-tanque-ondas | reutilizável | Markdown + scripts comuns |
| mcp-builder | reutilizável | Markdown + scripts comuns |
| memory-audit | reutilizável | Markdown + scripts comuns |
| mestre-direcao-dinamica | reutilizável | Markdown + scripts comuns |
| os-coach | reutilizável | Markdown + scripts comuns |
| pixflow-motion | reutilizável | Markdown + scripts comuns |
| pixflow-trailer | reutilizável | Markdown + scripts comuns |
| pp-skool | reutilizável | Markdown + scripts comuns |
| printing-press | adaptador | depende de MCP/conector do Claude |
| printing-press-catalog | adaptador | usa ferramenta/plugin exclusivo do Claude Code |
| printing-press-import | adaptador | usa ferramenta/plugin exclusivo do Claude Code |
| printing-press-output-review | reutilizável | Markdown + scripts comuns |
| printing-press-polish | adaptador | depende de MCP/conector do Claude |
| printing-press-publish | adaptador | usa ferramenta/plugin exclusivo do Claude Code |
| printing-press-reprint | adaptador | usa ferramenta/plugin exclusivo do Claude Code |
| printing-press-retro | adaptador | usa ferramenta/plugin exclusivo do Claude Code |
| printing-press-score | adaptador | usa ferramenta/plugin exclusivo do Claude Code |
| reel-edita-inema | reutilizável | Markdown + scripts comuns |
| reel-edita-inematds | reutilizável | Markdown + scripts comuns |
| remotion | reutilizável | Markdown + scripts comuns |
| remotion-best-practices | reutilizável | Markdown + scripts comuns |
| roteirista-inema | reutilizável | Markdown + scripts comuns |
| roteiro | reutilizável | Markdown + scripts comuns |
| scroll-film-studio | reutilizável | Markdown + scripts comuns |
| seedance-loop-prompt | reutilizável | Markdown + scripts comuns |
| session-handoff | reutilizável | Markdown + scripts comuns |
| session-statusline | reutilizável | Markdown + scripts comuns |
| silver-platter | nativo | depende de hook |
| skill-creator | reutilizável | Markdown + scripts comuns |
| theme-factory | reutilizável | Markdown + scripts comuns |
| ugc-seedance25 | adaptador | depende de MCP/conector do Claude |
| videoanima | reutilizável | Markdown + scripts comuns |
| video-demonstrativo | reutilizável | Markdown + scripts comuns |
| video-explicativo | reutilizável | Markdown + scripts comuns |
| video-ia | reutilizável | Markdown + scripts comuns |
| video-plan-editor | reutilizável | Markdown + scripts comuns |
| videoprodutor | reutilizável | Markdown + scripts comuns |
| videos-agnes | reutilizável | Markdown + scripts comuns |
| videos-cursos-inema | reutilizável | Markdown + scripts comuns |
| web-artifacts-builder | reutilizável | Markdown + scripts comuns |
| website-intelligence | adaptador | depende de MCP/conector do Claude |

## 3. Comandos, subagentes, hooks, plugins

| Ativo Claude | Qtd | Destino Codex | Classificação |
|---|---|---|---|
| slash commands (~/.claude/commands) | 0 | skills | reutilizável (vazio hoje) |
| subagentes (~/.claude/agents) | 7 | sem equivalente 1:1 | nativo — virar skill de 'papel' ou prompt |
| hooks (settings.json) | 2 | ~/.codex/hooks.json | adaptador — eventos diferem (Codex: PostToolUse, Stop) |
| plugins (enabledPlugins) | 7 | codex plugin | nativo |
| runbooks (~/.claude/runbooks) | 4 | context/ do projeto | reutilizável |
| CLAUDE.md global | 1 | AGENTS.md (+ resíduo Claude) | adaptador — ver scripts/adapt-instructions.sh |
| memória (~/.claude/projects/*/memory) | 219 projetos | context/ + handoffs/ | promoção manual, nunca cópia em massa |

## 4. Hooks do Codex hoje

```json
{
 "PostToolUse": [
  "Edit|Write|apply_patch"
 ],
 "Stop": [
  "*"
 ]
}
```

## 5. MCP (só nomes, sem valores)

- Claude (~/.claude.json global): magnific, metricool
- Codex (config.toml [mcp_servers]): nenhum

## 6. Não rodado / limitações

- Nenhum teste de comportamento foi executado por este script. Use `scripts/readback-test.sh` para evidência real.
- Classificação de skills é heurística por grep; revisar antes de migrar.
