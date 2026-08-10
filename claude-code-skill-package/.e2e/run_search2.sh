#!/usr/bin/env bash
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
  local label="$1"; local query="$2"; local limit="${3:-25}"
  local out=".e2e/searches/${label}.json"
  local tries=0
  while [ $tries -lt 4 ]; do
    local rev; rev=$(getrev)
    python "$HARNESS" --workspace "$WS" search-papers --run-id "$RUNID" --expected-revision "$rev" --query "$query" --limit "$limit" > "$out" 2>/dev/null
    if [ -s "$out" ] && python -c "import json; json.load(open('$out'))" 2>/dev/null; then
      python -c "
import json
d=json.load(open('$out')); r=d['result']
print(f'[$label] total={r[\"total_count\"]} hits={len(r[\"hits\"])} rev={r[\"state_revision\"]}')
for h in r['hits'][:15]:
    print(f\"  {h.get('publication_date','?')} | {h.get('arxiv_id','?')} | {h.get('title','?')[:60]}\")
"
      return 0
    fi
    tries=$((tries+1))
  done
  echo "[$label] FAILED (rev=$(getrev))"
  return 1
}
# Shorter, simpler queries to avoid INVALID_RESPONSE
run_search "s7_selfplay" "self-play language model" 25
run_search "s8_reward" "reward model language model" 25
run_search "s9_grpo" "group relative policy optimization" 25
run_search "s10_rag_rl" "reinforcement learning retrieval agent" 25
run_search "s11_deep_research" "deep research agent LLM" 25
run_search "s12_efficiency" "efficient reinforcement learning inference cost" 25
run_search "s13_benchmark" "agent benchmark evaluation search" 25
run_search "s14_offline_rl" "offline reinforcement learning language model" 25
