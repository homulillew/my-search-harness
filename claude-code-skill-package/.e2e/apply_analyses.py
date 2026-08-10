#!/usr/bin/env python3
"""FIXTURE / MECHANICAL SMOKE ONLY — not semantic Research Loop proof.

Applies a fixed batch of paper analyses via harness, tracking revision after each call.
This mechanically exercises put-paper-analysis at scale; it does NOT run an adaptive
research loop. Treat it as smoke tooling for the command surface, not as evidence of
correct loop discipline.
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

def get_current_revision():
    r = subprocess.run(
        ["python", HARNESS, "--workspace", WS, "view", "--run-id", RUN],
        capture_output=True, text=True, env=env, encoding="utf-8"
    )
    d = json.loads(r.stdout)
    return d["result"]["state_revision"]

def apply_analysis(input_file, expected_rev):
    r = subprocess.run(
        ["python", HARNESS, "--workspace", WS, "put-paper-analysis",
         "--run-id", RUN, "--expected-revision", str(expected_rev),
         "--input", input_file],
        capture_output=True, text=True, env=env, encoding="utf-8"
    )
    try:
        d = json.loads(r.stdout)
    except Exception:
        # stderr may have the JSON on encoding error
        try:
            d = json.loads(r.stderr)
        except Exception:
            return {"ok": False, "error": {"message": f"stdout={r.stdout[:200]} stderr={r.stderr[:200]}"}}
    return d

files = sorted(glob.glob(".e2e/analyses/*.json"))
print(f"Applying {len(files)} analyses...")

rev = get_current_revision()
print(f"Starting revision: {rev}")

ok_count = 0
fail_count = 0
for fn in files:
    aid = os.path.basename(fn).replace(".json","").replace("_",".")
    result = apply_analysis(fn, rev)
    if result.get("ok"):
        rev = result.get("result", {}).get("state_revision", rev)
        ok_count += 1
        print(f"  OK  {aid} -> rev {rev}")
    else:
        # Retry with fresh revision (RevisionConflictError)
        err = result.get("error", {})
        if "RevisionConflict" in str(err.get("type","")) or "expected revision" in str(err.get("message","")):
            rev = get_current_revision()
            result = apply_analysis(fn, rev)
            if result.get("ok"):
                rev = result.get("result", {}).get("state_revision", rev)
                ok_count += 1
                print(f"  OK  {aid} -> rev {rev} (retry)")
            else:
                fail_count += 1
                print(f"  FAIL {aid}: {result.get('error',{}).get('message','')[:120]}")
        else:
            fail_count += 1
            print(f"  FAIL {aid}: {result.get('error',{}).get('message','')[:120]}")

print(f"\nDone: {ok_count} ok, {fail_count} fail. Final revision: {rev}")
