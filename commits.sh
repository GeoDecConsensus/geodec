#!/usr/bin/env bash
#
# replay_commits.sh
#
# Usage: ./replay_commits.sh <n> <start-date>
#   <n>          Number of most‑recent commits to replay
#   <start-date> ISO date for the first new commit, e.g. "2025-04-01"
#
set -euo pipefail

if [[ $# -ne 2 || $1 =~ [^[:digit:]] ]]; then
  cat <<EOF
Usage: $0 <n> <start-date>
  <n>          positive integer (how many commits to copy & replay)
  <start-date> ISO date, e.g. 2025-04-01
EOF
  exit 1
fi

n=$1
start_date=$2

# GNU vs BSD date
if date --version >/dev/null 2>&1; then
  parse_date()  { date -d "$1" +%s; }
  format_date() { date -u -d "@$1" '+%Y-%m-%dT%H:%M:%SZ'; }
else
  parse_date()  { date -j -f '%Y-%m-%d' "$1" +%s; }
  format_date() { date -u -r "$1" '+%Y-%m-%dT%H:%M:%SZ'; }
fi

# 1. Capture the SHAs of the last n commits (chronological)
commits=( $(git rev-list --reverse HEAD~"$n"..HEAD) )
actual_n=${#commits[@]}
if [[ $actual_n -lt $n ]]; then
  echo "⚠️  Only found $actual_n commits; replaying $actual_n."
  n=$actual_n
else
  echo "✅ Found $n commits to replay."
fi

# 2. Compute base commit (HEAD~n) and create a fresh branch there
base_sha=$(git rev-parse HEAD~"$n")
echo "🔀 Resetting to $base_sha (HEAD~$n) on branch 'replay-$(date +%s)'" 
git checkout -b "replay-$(date +%s)" "$base_sha"

# 3. Seed our “current timestamp” and commit an explicit reset marker
current_ts=$(parse_date "$start_date")
iso_date=$(format_date "$current_ts")
GIT_AUTHOR_DATE="$iso_date" GIT_COMMITTER_DATE="$iso_date" \
  git commit --allow-empty -m "🔄 reset to $base_sha" --date "$iso_date"
echo " • [0 days] reset commit @ $iso_date"

echo "🗓️  Starting replay at $start_date; adding 5–10 day random gaps..."

# 4. Loop: for each original SHA, apply its diff and commit with same message+date
for sha in "${commits[@]}"; do
  # random 5–10 day gap
  gap_days=$(( RANDOM % 6 + 5 ))
  current_ts=$(( current_ts + gap_days * 86400 ))
  iso_date=$(format_date "$current_ts")

  # grab commit message
  msg=$(git log --format=%B -n1 "$sha")

  # apply exactly the same patch
  git diff "$sha^!" | git apply

  # stage and commit
  GIT_AUTHOR_DATE="$iso_date" GIT_COMMITTER_DATE="$iso_date" \
    git add -A
    git commit -m "$msg" --date "$iso_date"

  echo " • [+${gap_days}d] replay $sha → new commit @ $iso_date"
done

echo "🎉 Done: replayed $n commits (plus reset)."
echo "    New tip is $(git rev-parse HEAD)."