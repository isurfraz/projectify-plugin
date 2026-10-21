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
- Skills: `projectify`, `projectify-plan`, `projectify-next`, `projectify-handoff`.
