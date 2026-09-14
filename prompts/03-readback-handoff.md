# Prompts de verificação (fonte: docs/mega-prompts.pdf, p.10)

## Fresh-session readback

```text
Read this project's active instructions, current context, task, and latest handoff. Do not edit.
Report: (1) the current objective and acceptance criteria; (2) one important project rule,
with its exact source file; (3) the latest accepted decision; (4) the next concrete action; (5)
conflicts, stale facts, or missing access. Separate what the files establish from what you
infer. Do not rely on a previous conversation.

```

## Continuation handoff

```text
Create a concise continuation handoff for a fresh agent. Include the project and scope,
current objective, accepted state, changed files, checks actually run and their results, open
questions, and exact next action. Cite source paths and relevant revisions. Preserve
unresolved failures. Do not include credentials or claim that uncommitted changes are
available in another worktree. Update the current task/state only where the evidence
supports it.

```

## Required evidence

```text
A useful report distinguishes passed, failed and not-run checks. Verify standalone project
use, the representative task, active instructions, relevant skill/integration behavior and
client scope where applicable. A generated folder tree is not proof that an agent reads it or
that access is isolated.

```
