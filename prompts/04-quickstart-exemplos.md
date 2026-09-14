# Quick-start (modo audit) e exemplos preenchidos (fonte: docs/mega-prompts.pdf, p.9, 11-12)

## Migração — quick start

```text
Audit my existing Claude setup in [PROJECT_ROOT] for migration to [TARGET].

Inspect project instructions, skills, commands, agents, hooks, plugins, MCP, scripts, and memory
dependencies. Separate project assets from global settings. Check current target capabilities and any
earlier import results.

Return a source-to-destination matrix: reusable, adapter needed, native-only, or unresolved. Include the
proposed changes, rollback steps, and tests for [REAL_WORKFLOW]. Preserve my working Claude setup
and unrelated target settings.

Start in audit mode. Make no changes yet. Ask only for information that blocks the audit. Cite files; mark
unrun tests clearly.

Use full Prompt A for implementation requirements.
```

## Workspace — quick start

```text
Design a model-agnostic workspace in [WORKSPACE_ROOT] for [PERSONAL_OR_CLIENT] and pilot project
[PROJECT].

Target [TOOLS]. Keep private source knowledge separate from independent project repositories. Propose
a portable core for instructions, context, decisions, tasks, handoffs, skills, and scripts, with small native
adapters.

Show the folder hierarchy, source-of-truth owners, context refresh rules, and target compatibility. Do not
assume native memory, MCP, or model choices work identically across tools.

Start in audit mode. Return a concrete plan and tests for standalone project use, fresh-session readback,
and client scope where applicable. Make no changes yet.

Use full Prompt B plus the appropriate scope add-on for implementation.
```

## Exemplos preenchidos

```text
Existing Claude project
Use Prompt A. Paste this filled input block over its placeholders.

MODE: audit
WORKSPACE_ROOT: ./newsletter
SOURCE_ROOTS: ./newsletter
TARGETS: Codex CLI and Codex IDE
SCOPE: one project
REPRESENTATIVE_TASK: review a newsletter draft using our writing rules
KEEP_UNCHANGED: Claude workflow and existing files
CONSTRAINTS: inspect project configuration only

Personal second brain
Use Prompt B and append the personal add-on.

MODE: audit
WORKSPACE_ROOT: ./personal
WORKSPACE_TYPE: personal
PILOT_PROJECT: projects/newsletter
TARGETS: Claude Code, Codex, OpenCode + GLM
KNOWLEDGE_SOURCES: ./personal/brain
CLIENT_SCOPE: not applicable
REPRESENTATIVE_TASK: produce a draft using approved writing preferences

Client delivery workspace
Use Prompt B and append the client add-on.

MODE: audit
WORKSPACE_ROOT: ./clients/northstar
WORKSPACE_TYPE: client
PILOT_PROJECT: projects/website
TARGETS: Claude Code, Codex, Cowork
KNOWLEDGE_SOURCES: ./clients/northstar/knowledge
CLIENT_SCOPE: northstar
REPRESENTATIVE_TASK: review website copy against approved client standards
```
