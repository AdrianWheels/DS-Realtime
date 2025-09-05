# LocalVoiceTranslate Audio Router

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   LocalVoiceTranslate - Audio Router" -ForegroundColor Cyan  
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuraciones disponibles:" -ForegroundColor Yellow
Write-Host ""
Write-Host "[1] Micro G535 -> Auriculares G535" -ForegroundColor Green
Write-Host "[2] Micro G535 -> Altavoces PC" -ForegroundColor Magenta
Write-Host "[3] Ver dispositivos disponibles" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Elige una opcion (1-3)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "Iniciando: Micro G535 -> Auriculares G535" -ForegroundColor Green
    Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Yellow
    Write-Host ""
    .\.venv\Scripts\Activate.ps1
    python -m src.main --nogui --profile cpu-medium --input 8 --output 11
}
elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "Iniciando: Micro G535 -> Altavoces PC" -ForegroundColor Green
    Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Yellow
    Write-Host ""
    .\.venv\Scripts\Activate.ps1
    python -m src.main --nogui --profile cpu-medium --input 8 --output 13
}
elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "=== DISPOSITIVOS DISPONIBLES ===" -ForegroundColor Cyan
    .\.venv\Scripts\Activate.ps1
    python list_devices.py
    Write-Host ""
    Read-Host "Presiona Enter para salir"
}
else {
    Write-Host ""
    Write-Host "Opcion no valida" -ForegroundColor Red
}
