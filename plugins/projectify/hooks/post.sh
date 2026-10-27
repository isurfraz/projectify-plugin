#!/bin/sh
# Projectify fleet hooks (SPM-480, D-044, D-046): posts a Claude Code hook event to /v1/hooks/claude with this
# machine's token and prints the board's reply, which Claude Code reads as the hook's decision.
#
#   post.sh <EventName>   (the event JSON on stdin)
#
# SessionStart only prints a fleet worker's session id; the other events are posted.
#
# Only fleet workers are acted on: the API answers {} for any session start_session did not bind, so a
# person's own chats are never changed. Without a token, or outside a worktree, it posts nothing.
# Any failure prints nothing, so Claude Code falls back to its own behaviour (a terminal prompt).

data="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/projectify-projectify}"
token=$(cat "$data/token" 2>/dev/null)
[ -n "$token" ] || exit 0

input=$(cat)
# workers always run in a `claude --worktree` folder; skip the rest without a network call
case "$input" in
  *'/.claude/worktrees/'*) ;;
  *) exit 0 ;;
esac

# SessionStart: tell a worker its own session id (an agent body gets no ${CLAUDE_SESSION_ID}, and --bg ignores
# --session-id), so its start_session binds this session's hook events. Nothing is posted.
if [ "$1" = SessionStart ]; then
  case "$input" in
    *projectify-worker*) ;;
    *) exit 0 ;;
  esac
  sid=$(printf '%s' "$input" | sed -n 's/.*"session_id" *: *"\([0-9a-fA-F-]*\)".*/\1/p' | head -n 1)
  [ -n "$sid" ] && echo "Projectify fleet worker: this Claude Code session id is $sid. Pass it to start_session as claude_session_id."
  exit 0
fi

if [ -n "$PROJECTIFY_API" ]; then
  api="${PROJECTIFY_API%/}"
else
  api=$(sed -n 's#.*"url": *"\(https*://[^"]*\)/mcp/*".*#\1#p' "${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}/.mcp.json" 2>/dev/null | head -n 1)
  api="${api:-https://api.projectify.si}"
fi
api="${api%/v1}"

# a PermissionRequest is held on the board for up to 540 s (the hook's own timeout is 570 s)
case "$1" in
  PermissionRequest) wait=560 ;;
  *) wait=10 ;;
esac

printf '%s' "$input" | curl -sf --max-time "$wait" \
  -H "authorization: Bearer $token" \
  -H 'content-type: application/json' \
  --data-binary @- "$api/v1/hooks/claude" 2>/dev/null
exit 0
