---
name: projectify-learn
description: "Learn from a video, link, document or pictures and put it in Projectify: explain it to the person, and turn it into a team workflow (steps, prompts, checks) and techniques. Use when the person says \"explain this\", \"turn this into a workflow\", \"learn from\", \"make a workflow from\" or \"what does this video teach\", with a file on this computer or a link; also to build a playbook from several sources (\"learn from these ten videos\", \"build playbook PB-3\"), to follow one (\"using the UGC ads playbook, make…\"), to run a team workflow (\"do the weekly client report\", \"make me a cinematic ad\") or change one (\"add a sign-off before it goes out\")."
---

# Learn into Projectify

Explain a source, or turn it into a workflow the team and Claude can run again (any kind of work: a weekly report, a hire, a release, an ad). You read it here, more thoroughly than a server can: every word, and for a video the speech, every scene and the text on screen. Projectify shows the explainer filling in.

## Explain it or make a workflow
1. Call `learn` with the source ({kind, name, path or url}) and the goal (explain, or workflow when they said so). Given an explainer ref (EX-4)? `get_explainer` and carry on from its stages.
2. Follow its answer: how to read the source, the upload command, the shapes to write and their order, setting each stage with `update_explainer`. A failure is a stage set to failed with the reason in one line and the fixes; tell the person and stop guessing.
3. The reader: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/projectify-learn/analyse_media.py" <file or link> --out <folder>` (without the plugin: `curl -fsSL https://api.projectify.si/v1/public/learn/analyse_media.py -o analyse_media.py`). It needs python3 and ffmpeg; whisper.cpp (or mlx-whisper, openai-whisper, faster-whisper, or OPENAI_API_KEY), yt-dlp and tesseract make it better, and it says how to add each. Tell the person what is missing in one line and carry on.

## Several sources: a playbook (D-127)
- A playbook guides one area of work: which workflow or technique to use when, what always holds, the tools and the words. It points to workflows and techniques, never copies them.
- Two or more sources: `learn` with `sources` [..] and `playbook` {mode: playbook (the default) | best | each, focus}. "Build playbook PB-3": `get_playbook` with build: true. The answer says how to read, combine and save.
- Never average a disagreement away: record it in `conflicts` (every way, its sources, the one you chose and why). It is a draft until the person presses Mark ready.
- "Using the X playbook, make…": `get_playbook`, pick from its "Which to use" and tell the person why, then `run_workflow` with `playbook`, or `get_technique`. Nothing fits? Say so and ask; never improvise a process it does not have.

## Run and change workflows
- "Do the weekly client report": `list_workflows` with q (through `act`), then `run_workflow`. Each answer gives the step to do; report it with `update_run` (only the step the run is at; a check with state "review") and carry on with other runs while a check waits on the person.
- Per step: pick the best-value model you can use today, report `used` {model, why} and the real cost in `spent`. Not applicable: `state: "skipped"` with why. A phase done at once: `iteration: "all"` with `outputs` [{item, output}]. A step that is another workflow: `run_workflow` with `parent` {run, node}. Mid-run inputs: `update_run` `inputs`; files go up with the upload command, then in `files`. A scheduled run waiting in your briefing: tell your person, and do it when they say.
- Budget (D-119), only when steps have costs: ask what they will spend and pass `budget` [{amount, unit}]; at 100% it waits (raise it only with their words in `person_ok`). Inputs marked as variations make one output per combination.
- A changed copy ("every check Claude-only"): `get_flow` (raw: true), change the graph, `duplicate_workflow` with a note (through `act`). The workflow itself: `save_workflow` with workflow, base_version and a note.
- Only a person marks a workflow ready or answers a check (or you, quoting their answer). Checks handed to you for one run: `delegate_checks: true` with their words in `person_ok`, then pass each check against every criterion.
