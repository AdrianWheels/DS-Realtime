# LocalVoiceTranslate para Discord - Anti Bucles

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   LocalVoiceTranslate -> Discord" -ForegroundColor Cyan  
Write-Host "   MODO ANTI-BUCLES ACTIVADO" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "CONFIGURACION ANTI-BUCLES:" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ VAD Avanzado con supresion de ruido" -ForegroundColor Green
Write-Host "✅ Deteccion de nivel de volumen (-30dB minimo)" -ForegroundColor Green  
Write-Host "✅ Puerta de ruido (-45dB)" -ForegroundColor Green
Write-Host "✅ Cooldown de 500ms entre traducciones" -ForegroundColor Green
Write-Host "✅ Maximo 3 traducciones consecutivas" -ForegroundColor Green
Write-Host "✅ Duracion minima de voz: 300ms" -ForegroundColor Green
Write-Host ""
Write-Host "CONFIGURACION PARA DISCORD:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. LocalVoiceTranslate enviara audio a VB-Audio Point" -ForegroundColor Cyan
Write-Host "2. En Discord: Microfono = 'CABLE Output (VB-Audio Point)'" -ForegroundColor Cyan
Write-Host "3. IMPORTANTE: Baja el volumen de Discord en Windows" -ForegroundColor Red
Write-Host "   para evitar que se filtre de vuelta al micro" -ForegroundColor Red
Write-Host ""

$continuar = Read-Host "Presiona Enter para continuar o 'q' para salir"
if ($continuar -eq "q") { exit }

Write-Host ""
Write-Host "INICIANDO TRADUCTOR ANTI-BUCLES..." -ForegroundColor Green
Write-Host "Micro Logitech G535 (device 13) -> VB-Audio Point (device 40)" -ForegroundColor Cyan
Write-Host ""
Write-Host "DISCORD: Configura microfono como 'CABLE Output (VB-Audio Point)'" -ForegroundColor Yellow
Write-Host ""
Write-Host "CONSEJOS:" -ForegroundColor Magenta
Write-Host "- Habla claramente y con volumen normal" -ForegroundColor White
Write-Host "- Espera a que termine la traduccion antes de hablar de nuevo" -ForegroundColor White
Write-Host "- Si hay bucles, baja el volumen de Discord" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Red
Write-Host ""

.\.venv\Scripts\Activate.ps1
python -m src.main --nogui --profile cpu-medium --input 13 --output 40
