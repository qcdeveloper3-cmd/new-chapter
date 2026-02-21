$ErrorActionPreference = "Stop"

if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
    Write-Warning "VS Code CLI 'code' was not found in PATH. Skip extension install."
    exit 0
}

$extensionsConfig = Resolve-Path ".vscode/extensions.json"
$data = Get-Content -Raw $extensionsConfig | ConvertFrom-Json
$extensions = @($data.recommendations)

foreach ($ext in $extensions) {
    Write-Host "Installing VS Code extension: $ext"
    code --install-extension $ext --force | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Failed to install extension: $ext"
    }
}

Write-Host "VS Code extension install complete."
