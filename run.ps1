# Start Deployable-Knowledge on Windows (works offline after setup.ps1).
#   powershell -ExecutionPolicy Bypass -File .\run.ps1 [-Port 8000] [-Reload]
param([int]$Port = 8000, [switch]$Reload)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\venv\Scripts\python.exe")) { throw "No venv found. Run .\setup.ps1 first." }
if (-not (Test-Path ".\tmp_model\config.json")) { throw "Embedding model missing in .\tmp_model. Run .\setup.ps1 (needs internet once)." }

# Offline-friendly environment
$env:PYTHONUTF8 = "1"
$env:CHROMA_TELEMETRY_ENABLED = "false"
$env:ANONYMIZED_TELEMETRY = "False"
$env:TRANSFORMERS_OFFLINE = "1"
$env:HF_HUB_OFFLINE = "1"
$env:HF_DATASETS_OFFLINE = "1"

try {
    Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 3 | Out-Null
} catch {
    Write-Warning "Ollama does not seem to be running on localhost:11434. Search/upload will work, but chat needs Ollama."
}

$uvArgs = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port")
if ($Reload) { $uvArgs += "--reload" }
Write-Host "Open http://localhost:$Port in your browser (Ctrl+C to stop)."
& .\venv\Scripts\python.exe @uvArgs
