---
name: projectify-next
description: "Pick up and do work on a Projectify board: find the next task (next_task) or the one the person named, check what ranks above or blocks it, claim it, work it step by step, report progress and close it with an outcome. Use for \"what's next\", \"do ABC-12\", \"work the board\" or \"pick something up\"."
---

# Do the next task in Projectify

Open a session first (`start_session`) if you have none.

1. **Find it**: `get_task` the one named, else `next_task`.
2. **Check**: tell the person what ranks above it or blocks it; wait for their OK. Never take a task another chat holds, or touch its worktree or branch; if the person still wants it, `act("request_claim", { ref })`.
3. **Claim** with `claim_task({ ref, worktree, branch })` before changing anything. Refused because work ranks above? Ask; only on their yes claim again with `skip_reason` quoting them.
4. **Work** in small steps, following the sections claim_task hands you (`tidy_task` first when marked). Ask before building on a choice the person must make. `update_progress` at milestones; `update_task` tick_done_when as you verify.
5. **Room**, where there is one: a `say` line on start, before a shared change (heads_up), when blocked, when done.
6. **Blocked?** Stop, say it (blocker), set `needs_from_you`, ask and wait; never route around it, create tasks downstream of the blocker, or widen the task.
7. **Finish**: a person must look: `move_task` to In review with the reviewer and what to check. Else `move_task` to done with an outcome { shipped, verified, left_over }; at most one follow-up task.
