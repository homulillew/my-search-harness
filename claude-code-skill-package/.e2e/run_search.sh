#!/usr/bin/env bash
# FIXTURE / MECHANICAL SMOKE ONLY — not semantic Research Loop proof.
# Runs a fixed sequence of search-papers calls to populate a run for mechanical
# end-to-end smoke. This is a staged search batch, NOT an adaptive research loop.
# Per P0-D, a search call is not a research iteration; treat this as smoke tooling
# for the command surface, not as evidence of correct loop discipline.
set -uo pipefail
# DEEPXIV_TOKEN must be provided via environment; never hardcode the secret.
: "${DEEPXIV_TOKEN:?DEEPXIV_TOKEN not set in environment}"
export DEEPXIV_TOKEN
export PYTHONPATH=src
export CLAUDE_SKILL_DIR="$(pwd)/.claude/skills/literature-research"
HARNESS="$CLAUDE_SKILL_DIR/scripts/harness.py"
RUNID="run_b3d2057a-e66b-434b-aa2e-46b442a0bf58"
WS="workspace_e2e_rc"
getrev() { python "$HARNESS" --workspace "$WS" view --run-id "$RUNID" 2>/dev/null | python -c "import json,sys; print(json.load(sys.stdin)['result']['state_revision'])"; }

run_search() {
  local label="$1"; local query="$2"; local limit="${3:-25}"; local extra="$4"
  local rev; rev=$(getrev)
  local out=".e2e/searches/${label}.json"
  local tries=0
  while [ $tries -lt 4 ]; do
    rev=$(getrev)
    python "$HARNESS" --workspace "$WS" search-papers --run-id "$RUNID" --expected-revision "$rev" --query "$query" --limit "$limit" $extra > "$out" 2>/dev/null
    if [ -s "$out" ] && python -c "import json,sys; json.load(open('$out'))" 2>/dev/null; then
      python -c "
import json
d=json.load(open('$out'))
r=d['result']
print(f'[$label] total={r[\"total_count\"]} hits={len(r[\"hits\"])} rev={r[\"state_revision\"]}')
for h in r['hits']:
    print(f\"  {h.get('publication_date','?')} | {h.get('arxiv_id','?')} | {h.get('title','?')[:62]}\")
"
      return 0
    fi
    tries=$((tries+1))
  done
  echo "[$label] FAILED after retries (rev=$(getrev))"
  return 1
}

# Run the search series
run_search "s2_route_selfplay" "self-play reinforcement learning agent" 25 ""
run_search "s3_reward_design" "reward design reinforcement learning agent" 25 ""
run_search "s4_credit_assign" "credit assignment multi-step reinforcement learning" 25 ""
run_search "s5_search_control" "search depth control reinforcement learning agent" 25 ""
run_search "s6_tool_regulation" "tool use regulation reinforcement learning LLM" 25 ""
