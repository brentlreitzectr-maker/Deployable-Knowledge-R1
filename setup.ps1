# One-time setup for Windows (needs internet). Run from the repo folder:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = "1"

# Python packages (PyTorch in particular) contain very deep file paths. Unless Windows
# long paths are enabled, the project folder must have a short path or pip fails.
$longPaths = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name LongPathsEnabled -ErrorAction SilentlyContinue).LongPathsEnabled
if ($longPaths -ne 1 -and $PSScriptRoot.Length -gt 60) {
    throw ("This folder's path is $($PSScriptRoot.Length) characters long, which is too long for the Python packages " +
           "on Windows. Move the project to a short path such as C:\dk (or enable Windows long path support) and run setup again.")
}

# Pick a Python 3.11/3.12 interpreter (the pinned packages need >= 3.11)
$py = $null
foreach ($cand in @(@("py", "-3.12"), @("py", "-3.11"), @("python"))) {
    try {
        $v = & $cand[0] $cand[1..($cand.Length - 1)] -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
        if ($LASTEXITCODE -eq 0 -and $v -in @("3.11", "3.12")) { $py = $cand; break }
    } catch {}
}
if (-not $py) { throw "Python 3.11 or 3.12 not found. Install it with:  winget install -e --id Python.Python.3.12" }
Write-Host "Using Python $v"

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment in .\venv ..."
    & $py[0] $py[1..($py.Length - 1)] -m venv venv
    if ($LASTEXITCODE -ne 0) { Remove-Item -Recurse -Force .\venv -ErrorAction SilentlyContinue; throw "Creating the virtual environment failed" }
}
$vpy = ".\venv\Scripts\python.exe"

Write-Host "Installing Python packages (first run downloads ~1-2 GB, be patient) ..."
& $vpy -m pip install --upgrade pip
& $vpy -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

Write-Host "Downloading the embedding model into .\tmp_model ..."
& $vpy download_model.py
if ($LASTEXITCODE -ne 0) { throw "Model download failed" }

Write-Host ""
Write-Host "Setup complete. Next:"
Write-Host "  1. Install Ollama (https://ollama.com) and run:  ollama pull mistral:7b"
Write-Host "  2. Start the app:  powershell -ExecutionPolicy Bypass -File .\run.ps1"
