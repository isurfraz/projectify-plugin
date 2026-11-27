---
name: projectify-plan
description: "Define and plan work on a Projectify board before any task exists: restate the ask, size it S, M or L, walk the Define stages and their gates, then create one task or one epic with its tasks inside. Use when the person asks to plan, scope, spec or add a feature, epic or piece of work in Projectify."
---

# Plan work in Projectify

Define before you create: no task exists until the gates for its size are passed. Open a session first (`start_session`) if you have none.

1. `get_workflow({ project, moment: "defining" })` gives the project's Define stages and gates (by default: Intake and sizing → Goal and criteria → Discovery → Resolve blockers → Spec → Implementation plan → Validation plan → Board → Consistency check). Two gates are easy to miss: every criterion has a check (Validation), and the person said go before the first claim (Consistency check).
2. Read what exists so nothing is duplicated: the Brief, docs and decisions (`list_docs`), `search`, `list_tasks`, the code the work touches.
3. Walk the stages in order. At each gate, list its detail in your message, then ask one short question with your multiple-choice tool (`ask_question` when the person is not here), your pick first. Record their words as the approval (`update_task` approve, or on `create_task`).
4. Size: **S** is one task after Gate A; **M** one epic of several tasks; **L** adds a spec and a plan as docs (`create_doc`). Work needing a resource only some machines have (Higgsfield, Blender, Unity, a simulator) gets an epic of its own.
5. Create at the Board stage only. Each task: a **summary** (one plain sentence, no refs or code), ## Why, ## What, ## Done when (checkable), ## Not doing unless asked; `needs_from_you` when it needs a person.
6. Tell the person what ranks above it or blocks it, and wait for their go before anyone claims it.

Questions are asked, never stored as "Open questions". One request is one task or one epic (plus one per resource), never many top-level tasks.
