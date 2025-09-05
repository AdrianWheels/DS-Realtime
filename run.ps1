# Run script for LocalVoiceTranslate
# Usage: .\run.ps1 [-nogui]
param(
    [switch]$nogui
)

Set-Location $PSScriptRoot
if (-Not (Test-Path '.venv\Scripts\Activate.ps1')) {
    Write-Error ".venv not found. Create it with: py -3.11 -m venv .venv"
    exit 1
}

# Activate venv
. .\.venv\Scripts\Activate.ps1
# Ensure src is on PYTHONPATH
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')

if ($nogui) {
    python -m src.main --nogui
} else {
    python -m src.main
}
