# Start PyJarvis Service
# Run this in Terminal 1

Write-Host "Starting PyJarvis UI..." -ForegroundColor Green
Write-Host ""

python -m venv venv

cd $PSScriptRoot
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH="$PSScriptRoot"

pip install -r requirements.txt

python -m pyjarvis_ui

Write-Host "PyJarvis UI started successfully!" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow