#!/usr/bin/env python3
"""Apply approach families, findings, open problems, and gaps via harness.
Captures approach_ref from each family to link findings/open-problems.
"""
import json, subprocess, os, glob

HARNESS = ".claude/skills/literature-research/scripts/harness.py"
WS = "workspace_e2e_rc"
RUN = "run_b3d2057a-e66b-434b-aa2e-46b442a0bf58"

env = os.environ.copy()
# DEEPXIV_TOKEN must be provided via environment; never hardcode the secret.
if "DEEPXIV_TOKEN" not in env:
    raise RuntimeError("DEEPXIV_TOKEN not set in environment")
env["PYTHONUTF8"] = "1"

def run_cmd(args):
    r = subprocess.run(
        ["python", HARNESS, "--workspace", WS] + args,
        capture_output=True, text=True, env=env, encoding="utf-8"
    )
    try:
        return json.loads(r.stdout)
    except Exception:
        try:
            return json.loads(r.stderr)
        except Exception:
            return {"ok": False, "error": {"message": f"stdout={r.stdout[:200]} stderr={r.stderr[:200]}"}}

def get_rev():
    d = run_cmd(["view", "--run-id", RUN])
    return d["result"]["state_revision"]

def apply_with_retry(cmd, input_file, rev):
    d = run_cmd([cmd, "--run-id", RUN, "--expected-revision", str(rev), "--input", input_file])
    if not d.get("ok"):
        err = d.get("error", {})
        if "RevisionConflict" in str(err.get("type","")) or "expected revision" in str(err.get("message","")):
            rev = get_rev()
            d = run_cmd([cmd, "--run-id", RUN, "--expected-revision", str(rev), "--input", input_file])
    return d

rev = get_rev()
print(f"Starting revision: {rev}")

# 1. Apply approach families, capture refs
family_refs = []
fam_files = sorted(glob.glob('.e2e/landscape/family_*.json'))
for fn in fam_files:
    d = apply_with_retry("put-approach-family", fn, rev)
    if d.get("ok"):
        rev = d.get("result", {}).get("state_revision", rev)
        # Extract approach_ref
        af = d.get("result", {}).get("approach_family", {})
        aref = af.get("id") or af.get("approach_ref")
        family_refs.append(aref)
        print(f"  Family OK -> {aref} (rev {rev})")
    else:
        family_refs.append(None)
        print(f"  Family FAIL: {d.get('error',{}).get('message','')[:120]}")

print(f"Family refs: {family_refs}")

# 2. Apply findings (link to all families for now - cross-route findings)
finding_files = sorted(glob.glob('.e2e/landscape/finding_*.json'))
for fn in finding_files:
    # Inject approach_refs
    with open(fn, encoding='utf-8') as f:
        finding = json.load(f)
    finding["approach_refs"] = [r for r in family_refs if r]
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump(finding, f, ensure_ascii=False, indent=1)
    d = apply_with_retry("put-finding", fn, rev)
    if d.get("ok"):
        rev = d.get("result", {}).get("state_revision", rev)
        print(f"  Finding OK (rev {rev})")
    else:
        print(f"  Finding FAIL: {d.get('error',{}).get('message','')[:120]}")

# 3. Apply open problems
op_files = sorted(glob.glob('.e2e/landscape/openproblem_*.json'))
for fn in op_files:
    with open(fn, encoding='utf-8') as f:
        op = json.load(f)
    op["approach_refs"] = [r for r in family_refs if r]
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump(op, f, ensure_ascii=False, indent=1)
    d = apply_with_retry("put-open-problem", fn, rev)
    if d.get("ok"):
        rev = d.get("result", {}).get("state_revision", rev)
        print(f"  OpenProblem OK (rev {rev})")
    else:
        print(f"  OpenProblem FAIL: {d.get('error',{}).get('message','')[:120]}")

# 4. Apply gaps
gap_files = sorted(glob.glob('.e2e/landscape/gap_*.json'))
for fn in gap_files:
    d = apply_with_retry("put-gap", fn, rev)
    if d.get("ok"):
        rev = d.get("result", {}).get("state_revision", rev)
        print(f"  Gap OK (rev {rev})")
    else:
        print(f"  Gap FAIL: {d.get('error',{}).get('message','')[:120]}")

print(f"\nFinal revision: {rev}")
# Save family refs for later use
json.dump({"family_refs": family_refs, "final_rev": rev}, open('.e2e/landscape_refs.json','w',encoding='utf-8'), indent=1)
