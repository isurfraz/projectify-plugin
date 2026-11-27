# Projectify for Claude Code

Your Projectify board inside Claude Code: the board tools, a session hook that briefs every chat, and the Projectify skills.

## Install

```
/plugin marketplace add isurfraz/projectify-plugin
/plugin install projectify@projectify
```

Then run `/mcp`, pick the projectify server and choose Authenticate. You approve Claude in your browser.

For Claude Code on the web and cloud sessions, add Projectify as a connector on your Claude account instead (claude.ai › Settings › Connectors › Add custom connector, URL https://api.projectify.si/mcp). A cloud session cannot sign in with `/mcp`; the connector follows your account there.

## What you get

- The Projectify MCP server (https://api.projectify.si/mcp).
- A SessionStart hook: in any git repo it names the remote so Claude finds the project; quiet where the repo has its own Projectify hook.
- Skills: `projectify`, `projectify-plan`, `projectify-next`, `projectify-handoff`, `projectify-learn`.
- `/projectify:setup`: a few skippable questions, then Claude sets up your workspace and first project, and (optional) the fleet on this machine.
- The fleet: `projectify fleet` works the epics of every project with the fleet on, one `projectify-agent` background session per epic, each taking its epic from research to shipped. `projectify fleet doctor` checks this machine.

## Run the fleet

The fleet is optional and for Claude Code in a terminal. Workers run on your machine, on your Claude plan, and waiting for work costs no tokens.

1. **Install or update the plugin** in Claude Code: the two commands above, or `/plugin update projectify@projectify`. You need Node 18 or later and the GitHub CLI (`gh auth login`); workers open their pull requests with it.
2. **Set up this machine:** run `/projectify:setup` in any repo and say yes to the fleet. It saves this machine's token, runs `projectify setup-machine` (puts `projectify` in `~/.local/bin`, finds your project repos under `~/Documents/GitHub` and `~/code`, records and trusts each one) and ends with `projectify fleet doctor`. Repos somewhere else: `projectify setup-machine ~/src`.
3. **Switch projects on** in the web app: People › Fleet has a switch per project (projects start off) and each machine's worker cap. A project's Project settings › Fleet sets its limits, triggers, and the model and effort per role (with developer rules by task size or kind); People › Fleet › My defaults sets yours, and a fallback model. The launcher passes them as --model, --effort and --fallback-model. On a task, "Keep the fleet off this task" leaves it out, and Give to my fleet sends it next.
4. **Run it** in a terminal:

```
projectify fleet                 # every project with the fleet on and a repo here
projectify fleet SPM ABC         # only these projects
projectify fleet --dry-run       # what it would take, in order, then exit
projectify fleet --workers 2     # fewer workers than the machine cap, for this run
projectify fleet --until-empty   # exit when nothing is left to take or answer
projectify fleet --watch         # keep watching when idle (costs no tokens)
```

   Without --watch or --until-empty, the machine's "When there is nothing to do" setting in People › Fleet decides; the header says which. It prints the projects it works and the ones it skips (and why), then one line per event. Each worker is a full agent that takes one epic in its own worktree and does every step itself: research and define, plan, design, build, test, a fresh-eyes review by a subagent, and ship. Where merging is on (People › Fleet › Merging defaults, or the project's Project settings › Fleet) it merges its own PRs, one agent at a time; where it is off it leaves each PR In review for you. A risky step waits as an approval in Needs you on the web.
5. **Watch and stop:** `projectify fleet status` shows the workers; the project Overview and People › Fleet show the live fleet. Ctrl-C once stops after the current tasks, twice stops now; `projectify fleet stop [--now]` does the same from another terminal, and so does Stop on the live fleet in the web app.

**Full agents (Fleet 5):** there are no separate roles. Each worker slot is one `projectify-agent` that owns an epic end to end, so 2 workers work 2 epics side by side. Agents talk to each other through the project room and task comments, and decide for themselves what the task leaves open, writing "Assumed: …" on the task; only questions nobody but you can answer wait for you.

**What it takes:** epics, one agent each: an open epic with a ready task (unblocked, unclaimed and not needing a person) or with no tasks yet to flesh out, in a project with the fleet on, in Start next's order, taking turns across projects. Ready tasks in no epic are gathered into the project's Loose tasks epic.

**When something is off,** run `projectify fleet doctor`: one line per check, each with its fix. Three fixes are yours, in a terminal: `claude auth login` when Claude Code's own sign-in has expired (workers then stop on "OAuth session expired"), `claude mcp login plugin:projectify:projectify` (or `/mcp` → plugin:projectify:projectify → Authenticate) once, and `gh auth login`.

Notes: workers load no claude.ai connectors and use the plugin's Projectify server, not a repo's own `.mcp.json` one. Extra ask rules for workers go in `~/.claude/plugins/data/projectify-projectify/worker-settings.json`. The log is `fleet.log` in the same folder. `/plugin uninstall` deletes that folder, token included: run `/projectify:setup` again after a reinstall.
