---
name: projectify-handoff
description: "Wrap up a Projectify session: leave a note on each task you hold, write a handoff (done, unfinished, next) the next chat can pick up cold, and close with end_session. Use when the person says to hand off, wrap up, stop, end the session, or \"that's it for today\"."
---

# Hand off in Projectify

Leave the board so the next session, any person or Claude, can pick up from cold.

1. For each task you hold, say where it stands: a comment (`add_comment`), or pass it in `end_session`'s `notes` ({ "ABC-12": "branch pushed, PR open" }).
2. Write three short Markdown sections from what actually happened in this conversation:
   - done: what you finished, with task refs (e.g. "closed SUM-36, root-caused SUM-41").
   - unfinished: what is half-done and where it stands (branches, drafts, open questions).
   - next: what the next session should do first, and anything it must not do.
3. Learned something durable? Update the Brief or a doc (`get_doc`, then `edit_doc` with base_version) or record a decision (`record_decision`) with the alternatives you considered.
4. Created or changed an artifact, export or doc outside Projectify? Save it with `save_to_drive` and list it in `changed_sources` (or pass `[]`).
5. Post one line in the room (`say`, kind done) if others must pick something up.
6. Call `end_session({ handoff: { done, unfinished, next, touched }, notes, changed_sources })`. It releases your claims and saves the handoff in one call.
