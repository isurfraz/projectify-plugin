#!/bin/sh
# Projectify resource guard (SPM-963, D-138 §4): a PreToolUse hook for mcp__<server>__* calls. Asks
# /v1/tools/check whether this Claude Code session holds the lease on the app or simulator that MCP server
# drives, and refuses the call when another session holds it. A lease granted mid-session counts on the next
# call (the answer is never cached). Servers no resource names are allowed. For a pool (simulators) the call
# may not name another holder's device UDID (looked for in tool_input only, not in cwd or transcript_path).
#
# Fails open: no token, no network, or any odd reply allows the call (with a warning when the API is unreachable).

data="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/projectify-projectify}"
token=$(cat "$data/token" 2>/dev/null)
[ -n "$token" ] || exit 0

input=$(cat)
# Read the top-level fields, never ones nested in tool_input (a tool_input may carry its own "tool_name" or
# "session_id" key). node when present; else the first match, since Claude Code writes session_id first and
# tool_name before tool_input, and quotes inside strings are escaped so they cannot match.
first() { printf '%s' "$input" | grep -oE "\"$1\" *: *\"[^\"]*\"" | head -n 1 | sed -E 's/^[^:]*: *"(.*)"$/\1/'; }
if command -v node >/dev/null 2>&1; then
  parsed=$(printf '%s' "$input" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const j=JSON.parse(s);console.log(String(j.tool_name||""));console.log(String(j.session_id||""));console.log(JSON.stringify(j.tool_input===undefined?"":j.tool_input))}catch{}})' 2>/dev/null)
  tool=$(printf '%s\n' "$parsed" | sed -n 1p)
  sid=$(printf '%s\n' "$parsed" | sed -n 2p)
  args=$(printf '%s\n' "$parsed" | sed -n 3p)
else
  tool=$(first tool_name)
  sid=$(first session_id)
  args=$(printf '%s' "$input" | awk '{i=index($0,"\"tool_input\""); if(i) print substr($0,i)}')
fi
case "$tool" in mcp__*) ;; *) exit 0 ;; esac
server=${tool#mcp__}
server=${server%%__*}
# the board's own tools are never guarded
case "$server" in projectify|souls-pm|plugin_projectify_*|claude-in-chrome|claude-artifacts) exit 0 ;; esac
case "$sid" in *[!0-9a-fA-F-]*) sid= ;; esac
[ -n "$sid" ] || exit 0

if [ -n "$PROJECTIFY_API" ]; then
  api="${PROJECTIFY_API%/}"
else
  api=$(sed -n 's#.*"url": *"\(https*://[^"]*\)/mcp/*".*#\1#p' "${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}/.mcp.json" 2>/dev/null | head -n 1)
  api="${api:-https://api.projectify.si}"
fi
api="${api%/v1}"

reply=$(curl -sf --max-time 5 -G \
  -H "authorization: Bearer $token" \
  --data-urlencode "session=$sid" --data-urlencode "server=$server" \
  "$api/v1/tools/check" 2>/dev/null)
if [ -z "$reply" ]; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"Projectify could not be reached to check the lease on this tool; the call was allowed."}}'
  exit 0
fi

deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}\n' "$1"
  exit 0
}

case "$reply" in
  *'"allowed":false'*)
    reason=$(printf "%s" "$reply" | sed -n -E 's/.*"reason":("([^"\\]|\\.)*").*/\1/p' | head -n 1)
    deny "${reason:-\"This tool is held by another session; lease_tool to queue.\"}"
    ;;
esac

# a pool: the call may name only the holder's own device
udid=$(printf '%s' "$reply" | sed -n 's/.*"udid":"\([^"]*\)".*/\1/p' | head -n 1)
iname=$(printf '%s' "$reply" | sed -n 's/.*"instance":{"name":"\([^"]*\)".*/\1/p' | head -n 1)
if [ -n "$udid" ]; then
  others=$(printf '%s' "$args" | grep -oE '[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}' | grep -vF "$sid" | grep -viF "$udid" | head -n 1)
  if [ -n "$others" ]; then
    deny "\"This call names device $others, which this session does not hold. Your simulator is ${iname:-the one you leased} ($udid); use it, or lease_tool to queue for another.\""
  fi
fi
exit 0
