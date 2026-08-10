#!/usr/bin/env pwsh
# PowerShell setup for the standalone literature-research Skill.
#
# Equivalent to scripts/setup.sh: create a Skill-local venv, upgrade pip, and
# install the runtime requirements. The venv is created under the Skill directory
# so the harness launcher (scripts/harness.ps1) can find .venv\Scripts\python.exe
# without activating the environment. Run this once after installing the Skill;
# do not rebuild the venv on every research run.

$ErrorActionPreference = "Stop"

$SkillDir = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $SkillDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

# Prefer `python`; fall back to the py launcher so a Windows install that only
# exposes `py` still works. Either way the venv is self-contained afterwards.
function Resolve-BasePython {
    foreach ($candidate in @("python", "py")) {
        $found = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($found) {
            if ($candidate -eq "py") { return @($found.Source, "-3") }
            return @($found.Source)
        }
    }
    throw "python not found on PATH; install Python 3.11+ or add it to PATH."
}

$BasePython = Resolve-BasePython
& $BasePython[0] @($BasePython[1..($BasePython.Length - 1)]) -m venv $VenvDir

& $VenvPython -m pip install --upgrade pip

$Requirements = Join-Path $SkillDir "runtime\requirements.txt"
if (Test-Path $Requirements) {
    & $VenvPython -m pip install -r $Requirements
} else {
    # Match scripts/setup.sh for a source checkout before packaging.
    & $VenvPython -m pip install "deepxiv-sdk==0.3.1"
}

Write-Output "Standalone runtime ready. Set `$env:DEEPXIV_TOKEN in your shell, then run scripts/doctor.py."
