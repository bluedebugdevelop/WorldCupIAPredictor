# WorldCupIAPredictor - arranque en Windows (PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\backend

if (-not (Test-Path ".venv")) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -q -r requirements.txt

Write-Host "`nAbre http://127.0.0.1:8000 en el navegador`n" -ForegroundColor Green
uvicorn app.main:app --reload
