# LocalVoiceTranslate para Discord

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   LocalVoiceTranslate -> Discord" -ForegroundColor Cyan  
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "CONFIGURACION PARA DISCORD:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Este script enviara tu voz traducida a CABLE" -ForegroundColor Green
Write-Host "2. En Discord: Configurar microfono como 'CABLE Output'" -ForegroundColor Cyan
Write-Host "3. Opcional: En Windows configurar 'Listen to this device'" -ForegroundColor Gray
Write-Host "   para escuchar el audio en tus auriculares tambien" -ForegroundColor Gray
Write-Host ""

$continuar = Read-Host "Presiona Enter para continuar o 'q' para salir"
if ($continuar -eq "q") { exit }

Write-Host ""
Write-Host "INICIANDO TRADUCTOR..." -ForegroundColor Green
Write-Host "Micro Logitech G535 (device 13) -> VB-Audio Point (device 6)" -ForegroundColor Cyan
Write-Host ""
Write-Host "DISCORD: Configura microfono como 'CABLE Output (VB-Audio Point)'" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Red
Write-Host ""

.\.venv\Scripts\Activate.ps1
python -m src.main --nogui --profile cpu-medium --input 13 --output 6
