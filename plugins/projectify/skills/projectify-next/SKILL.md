---
name: projectify-next
description: "Pick up and do work on a Projectify board: find the next task (next_task) or the one the person named, check what ranks above or blocks it, claim it, work it step by step, report progress and close it with an outcome. Use for \"what's next\", \"do ABC-12\", \"work the board\" or \"pick something up\"."
---

# Do the next task in Projectify

Open a session first (start_session) if you have none.

1. **Find it.** The person named a task: `get_task` it. Otherwise call `next_task`, which gives the top free item from the shared queue people and agents pull from.
2. **Check before you start.** Tell the person in a line what ranks above it or blocks it, and wait for their OK. The briefing's "Working right now" lists tasks other chats hold: never take those, and never open, edit, commit in or delete another chat's worktree or branch. If the person still wants a held task, `act("request_claim", { ref })`.
3. **Claim it** with `claim_task({ ref, worktree, branch })` before changing anything. The lease renews on every call you make. If it is refused because work ranks above it, ask the person; only on their yes claim again with `skip_reason` quoting them. Never invent their OK.
4. **Follow the sections claim_task hands you** (Feature, Bugfixing, Spike…). A task marked to tidy is tidied first (`tidy_task`).
5. **Say it in the room** in one line (`say`) when you start, before a change others depend on (schema, a shared package, an API, config, deploy: kind heads_up), when blocked (blocker) and when done.
6. **Work in small steps.** Ask before you build on a choice the person must make. At milestones (branch pushed, PR open, blocked) call `update_progress`. Tick done-when items as you verify them (`update_task` tick_done_when).
7. **Blocked?** Stop, say it (kind blocker), set `needs_from_you`, ask the question and wait. Never create tasks downstream of a blocker or widen the task to route around it.
8. **Finish.** A person needs to look: `move_task` to In review with the reviewer and what they check. Done: `move_task` to done with an outcome { shipped, verified, left_over }. Anything left over is one follow-up task at most.

Then pick the next one, or wrap up with the handoff.
