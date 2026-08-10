#!/usr/bin/env pwsh
# PowerShell launcher for the literature-research harness.
#
# Mirrors scripts/harness (Bash): resolve the Skill root, prefer the Skill-local
# venv, fall back to a system Python, then delegate to the same harness.py so all
# research logic runs through one Python entry point. Passes arguments verbatim
# and propagates the exit code.

$ErrorActionPreference = "Stop"

if ($env:CLAUDE_SKILL_DIR) {
    $SkillDir = (Resolve-Path $env:CLAUDE_SKILL_DIR).Path
} else {
    $SkillDir = Split-Path -Parent $PSScriptRoot
}

$VenvPython = Join-Path $SkillDir ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

$HarnessScript = Join-Path $PSScriptRoot "harness.py"

& $Python $HarnessScript @args
exit $LASTEXITCODE
