# Projectify for Claude Code

Generated from `packages/shared/src/skills.ts` in the Projectify repo by `scripts/build-plugin.ts`. Do not edit by hand.

## Install

```
/plugin marketplace add isurfraz/projectify-plugin
/plugin install projectify@projectify
```

Then run `/mcp`, pick the souls-pm server and choose Authenticate. You approve Claude in your browser.

## What you get

- The Projectify MCP server (https://api.projectify.si/mcp).
- A SessionStart hook: in any git repo it names the remote so Claude finds the project; quiet where the repo has its own Projectify hook.
- Skills: `projectify`, `projectify-plan`, `projectify-next`, `projectify-handoff`.
