---
name: projectify-handoff
description: "Wrap up a Projectify session: leave a note on each task you hold, write a handoff (done, unfinished, next) the next chat can pick up cold, and close with end_session. Use when the person says to hand off, wrap up, stop, end the session, or \"that's it for today\"."
---

# Hand off in Projectify

So the next session, person or Claude, can pick up cold:

1. Each task you hold: where it stands, in `end_session` `notes` ({ "ABC-12": "PR open" }) or `add_comment`.
2. Write three short Markdown sections from what actually happened in this conversation:
   - done: what you finished, with task refs (e.g. "closed SUM-36, root-caused SUM-41").
   - unfinished: what is half-done and where it stands (branches, drafts, open questions).
   - next: what the next session should do first, and anything it must not do.
3. Durable learnings: `get_doc` the Brief or a doc, then `edit_doc` with its `base_version`; a decision with `record_decision`.
4. Changed something outside Projectify? `save_to_drive` it; list it in `changed_sources` (else `[]`).
5. Others must pick something up? One `say` line (kind done).
6. `end_session({ handoff: { done, unfinished, next, touched }, notes, changed_sources })`: it releases your claims.
