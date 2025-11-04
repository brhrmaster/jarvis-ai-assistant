# Script para testar o fluxo de áudio
# Inicia service, UI e CLI em janelas separadas

Write-Host "=== Iniciando PyJarvis Test Flow ===" -ForegroundColor Cyan

# Função para abrir uma nova janela do PowerShell
function Start-InNewWindow {
    param(
        [string]$Command,
        [string]$Title
    )
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; $Command; Write-Host '`nPressione qualquer tecla para fechar...'; $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"
}

# Janela 1: Service
Write-Host "Iniciando Service em nova janela..." -ForegroundColor Yellow
Start-InNewWindow -Command "python -m pyjarvis_service" -Title "PyJarvis Service"

# Aguardar um pouco para o service inicializar
Start-Sleep -Seconds 3

# Janela 2: UI
Write-Host "Iniciando UI em nova janela..." -ForegroundColor Yellow
Start-InNewWindow -Command "python -m pyjarvis_ui" -Title "PyJarvis UI"

# Aguardar um pouco para a UI inicializar
Start-Sleep -Seconds 2

# Janela 3: CLI Test
Write-Host "Iniciando CLI test em nova janela..." -ForegroundColor Yellow
Start-InNewWindow -Command "python -m pyjarvis_cli 'Hello, this is a test message to analyze audio flow'" -Title "PyJarvis CLI Test"

Write-Host "`n=== Serviços iniciados em janelas separadas ===" -ForegroundColor Green
Write-Host "Analise os logs em cada janela para identificar problemas." -ForegroundColor Cyan
Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

