#!/bin/sh
# Projectify fleet statusline (SPM-480, FLEET-PLAN §3.7): the launcher passes it to every worker with --settings.
# It saves the plan use Claude Code reports to <data>/quota.json ({five_hour, seven_day}, whole percentages),
# which the launcher's heartbeat sends so the board can stop the fleet at the project's plan-use limit.
#
#   statusline.sh <data folder>   (Claude Code's statusline JSON on stdin)

data="${1:-${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/projectify-projectify}}"
exec node -e '
const fs = require("fs");
const path = require("path");
let raw = "";
process.stdin.on("data", (d) => (raw += d)).on("end", () => {
  let j = {};
  try { j = JSON.parse(raw); } catch {}
  // rate_limits is null until the first API response; a window is a number or { used_percentage }
  const pct = (w) => {
    const v = typeof w === "number" ? w : w && typeof w === "object" ? w.used_percentage ?? w.utilization ?? w.percent : null;
    return typeof v === "number" && isFinite(v) ? Math.max(0, Math.min(100, Math.round(v))) : null;
  };
  const r = j.rate_limits;
  const q = r ? { five_hour: pct(r.five_hour), seven_day: pct(r.seven_day) } : null;
  if (q && (q.five_hour !== null || q.seven_day !== null)) {
    try {
      const dir = process.argv[1];
      fs.mkdirSync(dir, { recursive: true });
      const tmp = path.join(dir, `quota.json.${process.pid}`);
      fs.writeFileSync(tmp, JSON.stringify({ ...q, at: new Date().toISOString() }));
      fs.renameSync(tmp, path.join(dir, "quota.json"));
    } catch {}
  }
  const model = j.model?.display_name ?? "";
  const use = q ? ` · plan ${q.five_hour ?? "?"}% 5h, ${q.seven_day ?? "?"}% 7d` : "";
  process.stdout.write(`projectify worker${model ? ` · ${model}` : ""}${use}`);
});
' "$data"
