---
name: projectify-plan
description: "Define and plan work on a Projectify board before any task exists: restate the ask, size it S, M or L, walk the Define stages and their gates, then create one task or one epic of at most 5 tasks. Use when the person asks to plan, scope, spec or add a feature, epic or piece of work in Projectify."
---

# Plan work in Projectify

Define before you create: no task exists until the gates for its size are passed. Open a session first (start_session) if you have none.

1. Read the project's own Define stages with `get_workflow({ project, moment: "defining" })`. They are this workspace's version and win over the outline below.
2. Read what exists so nothing is duplicated: the Brief, Knowledge, Decisions, `search` and `list_tasks`, and the code the work touches.
3. Walk the stages in order. Ask at each gate with your multiple-choice tool (AskUserQuestion in Claude Code; `ask_question` when the person is not in this chat), the option you recommend first. Record their words as the approval (`update_task` approve, or on `create_task`).
4. Size decides how far you go: **S** (a fix or tweak under one session) is one task after Gate A. **M** is one epic with 2 to 5 tasks. **L** adds a spec and a plan as Knowledge notes (`create_doc`).
5. Create the work only at the Board stage. Every task carries a **summary** (one plain sentence a newcomer understands, no refs or code), ## Why, ## What, ## Done when (at most 5 checkable items) and ## Not doing unless asked. Set `needs_from_you` when it needs a person.
6. Tell the person what ranks above the new work or blocks it, and wait for their go before anyone claims it.

## The Define stages (default outline)
- **Define 0 · Intake and sizing**: A person asks for work and chooses the Projectify workflow. Gate: the ask is restated in plain words; the person confirmed the ask, size, goal and criteria.
- **Define 1 · Goal and criteria**: M and L work, after intake. Gate: a one-sentence goal; success criteria, 1 to 5.
- **Define 2 · Discovery**: M and L work; S when something is unclear.
- **Define 3 · Resolve blockers**: Any open blocker from discovery. Gate: no open blockers.
- **Define 4 · Spec**: M and L work. Gate: the person approved the spec and frames.
- **Define 5 · Implementation plan**: M and L work. Gate: the plan fits the caps.
- **Define 6 · Validation plan**: Every size. Gate: every criterion has a check.
- **Define 7 · Board**: After the gates above.
- **Define 8 · Consistency check**: M and L work, before the first claim. Gate: the person said go.

Never leave an "Open questions" section: a question is asked, not stored. Never create many top-level tasks: one request is one task, or one epic.
