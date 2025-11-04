# Start PyJarvis Service
# Run this in Terminal 1

Write-Host "Starting PyJarvis Service..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

cd $PSScriptRoot
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH="$PSScriptRoot"
python -m pyjarvis_service



