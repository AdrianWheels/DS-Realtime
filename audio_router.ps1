# LocalVoiceTranslate Audio Router
# Configuración avanzada de audio routing

param(
    [string]$Mode = "menu",
    [int]$InputDevice = 8,
    [int]$OutputDevice = 11,
    [string]$Profile = "cpu-medium"
)

function Show-Menu {
    Clear-Host
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "   LocalVoiceTranslate - Audio Router" -ForegroundColor Cyan  
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Configuraciones rápidas:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "[1] 🎧 Micro G535 → Auriculares G535" -ForegroundColor Green
    Write-Host "[2] 🎮 Micro G535 → CABLE (Discord)" -ForegroundColor Blue
    Write-Host "[3] 🔊 Micro G535 → Altavoces PC" -ForegroundColor Magenta
    Write-Host "[4] 📋 Ver dispositivos disponibles" -ForegroundColor White
    Write-Host "[5] ⚙️  Configuración manual" -ForegroundColor Gray
    Write-Host "[6] 🚪 Salir" -ForegroundColor Red
    Write-Host ""
}

function Start-Translation {
    param($InputId, $OutputId, $Description)
    
    Write-Host ""
    Write-Host "🚀 Iniciando: $Description" -ForegroundColor Green
    Write-Host "📥 Entrada: Dispositivo $InputId" -ForegroundColor Cyan
    Write-Host "📤 Salida: Dispositivo $OutputId" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Yellow
    Write-Host ""
    
    & .\.venv\Scripts\Activate.ps1
    python -m src.main --nogui --profile $Profile --input $InputId --output $OutputId
}

function Show-Devices {
    Write-Host ""
    Write-Host "=== DISPOSITIVOS DISPONIBLES ===" -ForegroundColor Cyan
    & .\.venv\Scripts\Activate.ps1
    python list_devices.py
    Write-Host ""
    Read-Host "Presiona Enter para continuar"
}

if ($Mode -eq "direct") {
    Start-Translation -InputId $InputDevice -OutputId $OutputDevice -Description "Configuración personalizada"
    return
}

while ($true) {
    Show-Menu
    $choice = Read-Host "Elige una opción (1-6)"
    
    switch ($choice) {
        1 { 
            Start-Translation -InputId 8 -OutputId 11 -Description "Micro G535 → Auriculares G535"
            break
        }
        2 { 
            Write-Host ""
            Write-Host "ℹ️  NOTA: En Discord, configura el micrófono como 'CABLE Output'" -ForegroundColor Yellow
            Start-Translation -InputId 8 -OutputId "CABLE Input" -Description "Micro G535 → CABLE (Discord)"
            break
        }
        3 { 
            Start-Translation -InputId 8 -OutputId 13 -Description "Micro G535 → Altavoces PC"
            break
        }
        4 { 
            Show-Devices
        }
        5 {
            Write-Host ""
            $customInput = Read-Host "ID del dispositivo de entrada"
            $customOutput = Read-Host "ID del dispositivo de salida"
            Start-Translation -InputId $customInput -OutputId $customOutput -Description "Configuración manual"
            break
        }
        6 { 
            Write-Host ""
            Write-Host "¡Hasta luego! 👋" -ForegroundColor Green
            return
        }
        default { 
            Write-Host ""
            Write-Host "❌ Opción no válida" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}
