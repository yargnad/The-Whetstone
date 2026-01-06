# Run script for The Whetstone (PowerShell)
# Usage: .\run.ps1 [-Model qwen3:8b] [-Backend ollama]
param(
    [string]$Model = "qwen3:8b",
    [string]$Backend = "ollama"
)

# Optionally adjust these paths
$venvPath = ".\.venv\Scripts\Activate.ps1"

Write-Host "Setting runtime environment..."
$env:WHETSTONE_MODEL = $Model
$env:WHETSTONE_BACKEND = $Backend

if (Test-Path $venvPath) {
    Write-Host "Activating virtualenv..."
    . $venvPath
} else {
    Write-Host "No .venv found. Create one with: py -3 -m venv .venv"
}

Write-Host "Starting The Whetstone (model=$Model backend=$Backend)..."
python .\tui_app.py
