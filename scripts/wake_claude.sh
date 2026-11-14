#!/usr/bin/env bash
# Start the Claude Code task right away (its API trigger). This is the only way Claude starts on its own: there is
# no hourly run. Needs repo secrets CLAUDE_TASK_URL (the task's "Fire URL") and CLAUDE_TASK_TOKEN.
#   Usage: scripts/wake_claude.sh "<why>" [<issue number>]
# Never fails the workflow (always exit 0). The outcome is written to $WAKE_OUT/wake_status (default /tmp):
#   ok        Claude was called
#   busy      not called: the issue has an arc-busy label added less than 2 hours ago (a Claude chat or task is
#             working on it and continues by itself), so nothing is said on the issue either
#   nosecret  the two secrets are missing
#   failed    the call was refused or the network failed, after 3 tries
# and $WAKE_OUT/wake_note holds one Vietnamese sentence for the owner when Claude was not called (empty otherwise).
# With an issue number (needs GH_TOKEN and GH_REPO or GITHUB_REPOSITORY) that sentence is posted on the issue as a
# 🤖 comment, unless WAKE_COMMENT=0: then the caller puts wake_note into its own comment.
set -u
WHY="${1:-}"; N="${2:-}"
OUT="${WAKE_OUT:-/tmp}"
REPO="${GH_REPO:-${GITHUB_REPOSITORY:-}}"
BUTTON="${GITHUB_SERVER_URL:-https://github.com}/$REPO/actions/workflows/wake.yml"
case "$N" in ''|*[!0-9]*) N="";; esac

finish() {   # finish <status> [<note for the owner>]
  printf '%s\n' "$1" > "$OUT/wake_status"; printf '%s' "${2:-}" > "$OUT/wake_note"
  if [ -n "${2:-}" ] && [ -n "$N" ] && [ -n "$REPO" ] && [ -n "${GH_TOKEN:-}" ] && [ "${WAKE_COMMENT:-1}" != 0 ]; then
    gh api -X POST "repos/$REPO/issues/$N/comments" -f body="🤖 $2" > /dev/null \
      || echo "::warning::wake: không ghi được bình luận lên phiếu $N"
  fi
  exit 0
}

busy_fresh() {   # arc-busy is on the issue now and was added less than 2 hours ago
  [ -n "$N" ] && [ -n "$REPO" ] && [ -n "${GH_TOKEN:-}" ] || return 1
  gh api "repos/$REPO/issues/$N/labels?per_page=100" --jq '.[].name' 2>/dev/null | grep -qx arc-busy || return 1
  local t
  t=$(gh api "repos/$REPO/issues/$N/events?per_page=100" --paginate \
        --jq '.[] | select(.event == "labeled" and .label.name == "arc-busy") | .created_at' 2>/dev/null | tail -n 1)
  [ -n "$t" ] || return 1
  python3 -c 'import sys, datetime as d
t = d.datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00"))
sys.exit(0 if (d.datetime.now(d.timezone.utc) - t).total_seconds() < 7200 else 1)' "$t"
}

if busy_fresh; then
  echo "wake: phiếu $N đang có nhãn arc-busy (dưới 2 giờ) — Claude đang làm phiếu này, không gọi thêm."
  finish busy
fi

[ -n "${CLAUDE_TASK_URL:-}" ] && [ -n "${CLAUDE_TASK_TOKEN:-}" ] || {
  echo "::warning::Chưa cài CLAUDE_TASK_URL/CLAUDE_TASK_TOKEN: chưa gọi được Claude. Phiếu chờ đến khi thêm hai secret này rồi bấm Gọi Claude ngay, hoặc làm trong chat."
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    printf '\n### Chưa gọi được Claude ngay\nThêm secrets `CLAUDE_TASK_URL` và `CLAUDE_TASK_TOKEN` (API trigger của tác vụ Claude chung, cùng giá trị như repo văn học) để Claude bắt đầu ngay khi có việc. Không có lượt chạy mỗi giờ: hiện phiếu chờ đến khi bấm **Gọi Claude ngay** hoặc làm trong chat.\n' >> "$GITHUB_STEP_SUMMARY"
  fi
  finish nosecret "Chưa gọi được Claude: repo này chưa có hai khóa \`CLAUDE_TASK_URL\` và \`CLAUDE_TASK_TOKEN\` (xem README, mục Cấu hình). Phiếu đang chờ: thêm hai khóa đó rồi bấm **Gọi Claude ngay** → Run workflow ($BUTTON), hoặc mở một chat với Claude để làm tiếp."
}

BODY=$(printf '%s' "$WHY" | python3 -c 'import json,sys;print(json.dumps({"text":sys.stdin.read()[:300]}))')
CODE=000
for i in 1 2 3; do
  CODE=$(curl -s -o "$OUT/wake.json" -w '%{http_code}' --max-time 30 -X POST "$CLAUDE_TASK_URL" \
    -H "Authorization: Bearer $CLAUDE_TASK_TOKEN" \
    -H "anthropic-beta: experimental-cc-routine-2026-04-01" -H "anthropic-version: 2023-06-01" \
    -H "Content-Type: application/json" -d "$BODY") || true
  case "$CODE" in
    2*) echo "wake: Claude đã được gọi ($(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('claude_code_session_url',''))" "$OUT/wake.json" 2>/dev/null))"
        finish ok ;;
    000|429|5*) ;;        # network error, rate limit, server error: worth another try
    *) break ;;           # 4xx: wrong URL or token, a retry cannot help
  esac
  [ "$i" = 3 ] || { echo "wake: lần $i không được (HTTP $CODE), thử lại"; sleep $((i * 10)); }
done
echo "::warning::wake: gọi Claude không được (HTTP $CODE) — bấm Gọi Claude ngay sau, hoặc làm trong chat"
head -c 300 "$OUT/wake.json" 2>/dev/null; echo
finish failed "Chưa gọi được Claude (lỗi $CODE khi gọi, có thể do hết hạn mức hoặc mạng). Phiếu đang chờ: bấm **Gọi Claude ngay** → Run workflow ($BUTTON), hoặc mở một chat với Claude để làm tiếp."
