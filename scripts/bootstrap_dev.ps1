param(
    [switch]$InstallOptionalEngines,
    [switch]$InstallVSCodeExtensions,
    [switch]$ForceSkillOverwrite
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

if (-not (Test-Path ".venv/Scripts/python.exe")) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.12 -m venv .venv
    } else {
        python -m venv .venv
    }
}

$pythonExe = Resolve-Path ".venv/Scripts/python.exe"

# Avoid local proxy issues during package installation unless explicitly needed.
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""

& $pythonExe -m pip install --upgrade pip setuptools wheel
& $pythonExe -m pip install -e ".[dev]"
if ($InstallOptionalEngines) {
    & $pythonExe -m pip install -e ".[analysis,fallback]"
}

& $pythonExe -m pre_commit install

$skillArgs = @("scripts/install_repo_skills.py")
if ($ForceSkillOverwrite) {
    $skillArgs += "--force"
}
& $pythonExe $skillArgs

if ($InstallVSCodeExtensions) {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_vscode_extensions.ps1
}

Write-Host "Bootstrap complete."
