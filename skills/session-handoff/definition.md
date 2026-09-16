---
identity:
  name: session-handoff
  description:
    full: >-
      Use when the user wants to end a session and hand off context to a future agent. Triggers
      include "session handoff", "handoff", "wrap up", "wrap up session", "vou dar /clear",
      "encerrar sessão", "passar para outro agente", "resumo final antes de limpar", "summarize
      before clear". Produces a chat-only structured handoff so a fresh agent can continue without
      losing continuity.
activation:
  triggers: []
  auto_invoke: true
  user_invoke: true
  context_isolation: false
dependencies:
  mcp: []
  bash: []
  env: []
resources:
  scripts: []
  references: []
  assets: []
behavior:
  dynamic_injections: []
constraints:
  max_body_lines: 500
  recommended_body_tokens: 5000
---

# Session Handoff

Produce a repeatable end-of-session summary so the user can `/clear` and start a fresh agent without losing continuity. The next agent should be able to pick up by reading this summary alone.

This is a **context-handoff artifact**, not a status report. The audience is a future instance of you, not a stakeholder.

## When to invoke

User says any of: "session handoff", "handoff", "wrap up", "wrap up session", "vou dar /clear", "encerrar sessão", "passar para outro agente", "resumo final antes de limpar", "summarize before clear".

**On `/clear` intent:**
- Clear intent ("vou dar /clear", "vou limpar agora") with active work → run handoff directly.
- Vague intent ("talvez eu limpe", "acho que vou clear") → ask once: "rodar handoff antes?"

Do NOT invoke for "organiza/otimiza a sessão" — those go to `session-statusline`. Do NOT invoke for "analise a memória" / "CLAUDE.md" — those go to `memory-audit`.

## How to produce the summary

1. **Review the full conversation**, not just the last few turns. Handoffs miss things when they only summarize recent context.
2. **For long conversations (>50 turns):** focus on inflection points — direction changes, reverted decisions, current state — not chronological narration.
3. **Pull state from these sources (in order):**
   - Plan files referenced this session (check `~/.claude/plans/` if a plan was mentioned).
   - Task list state — any in-progress or pending tasks.
   - Background processes you started with `run_in_background` — shell IDs are load-bearing for the next agent.
   - Files created or modified this session — you know what you touched; don't grep to re-discover.
   - Memory files written or updated (`~/.claude/projects/<project>/memory/`).
   - Unresolved questions — things you asked the user that never got a clear answer, or things the user asked that got deflected.
4. **Do NOT audit the filesystem.** This is synthesis of what happened in THIS session. No `git log`, no broad `Glob` sweeps. If you didn't touch it this session, it doesn't belong here.
5. **Don't include exploration noise** — failed greps, discarded attempts, context the next agent reconstructs by reading the listed files.
6. **Produce the output in chat.** Do not write a file. Do not update memory. Chat-only.

## Confidence markers

Prefix uncertain items so the next agent knows what to verify:

- `[confirmed]` — fato verificado nesta sessão
- `[unverified]` — provável, mas não confirmado
- `[?]` — incerto, depende de checagem pelo próximo agente

## Output template — use exactly this structure, every time

```
# Session Handoff — <one-line title of what this session was about>

## Where it started
<2-3 sentences: what the user asked for, key framing or constraints that emerged>

## Applied / shipped
- [confirmed] <change> — <where it lives, absolute path>
- ...

## Proposed / attempted but not confirmed
- [unverified] <proposal or partial change> — <why not confirmed>
- [?] <uncertain item> — <what to check>
- (or "none")

## Key files for next session
- `<absolute path>` — <why the next agent should read this first>
- Plan file: `<path>` (or "none")
- Memory files touched: `<paths>` (or "none")

## Running state
- Background processes: <shell IDs + what they are + how to kill> (or "none")
- Dev servers / ports: <url + port> (or "none")
- Open worktrees / branches: <paths> (or "none")

## Verification — how to confirm things still work
- `<command>` — <expected outcome>
- ...

## Deferred + open questions
- Deferred: <item> — <why pushed to later>
- Open: <question needing the user's input> — <context>

## Pick up here
<1-3 lines: most likely next action. If branching, list the branches explicitly (e.g., "A se teste passar, B se falhar").>
```

## Rules

1. **Chat output only.** Never write the handoff to a file. Never update memory from this skill.
2. **Never invent state.** If a section has nothing to report, write "none" — do not omit the section. Structure stability is the whole point.
3. **Absolute paths always.** The next agent may have a different working directory.
4. **If a plan file drove the session, name it first** in "Key files" so the next agent reads it before anything else.
5. **Background process IDs are critical.** If you started any `run_in_background` shells, their IDs must appear in "Running state" with the kill command — the next agent cannot find them otherwise.
6. **No emojis, no hype, no retrospective.** Terse and concrete — paths, commands, shell IDs, decisions. Match the tone of a seasoned engineer handing off at end-of-shift.
7. **No "what went well / what went poorly".** This isn't a retro.
8. **No recommendations beyond the single "Pick up here" line.** The next agent decides; you just hand off.
