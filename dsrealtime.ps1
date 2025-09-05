# DSRealtime - Utilidades de Gestión
# Versión consolidada que reemplaza múltiples scripts

param(
    [string]$Action = "menu",
    [int]$InputDevice,
    [int]$OutputDevice,
    [string]$Profile = "cpu-medium"
)

function Show-MainMenu {
    Clear-Host
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "   DSRealtime - Control Central" -ForegroundColor Cyan  
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🚀 Configuraciones rápidas:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "[1] 🎧 Micro G535 → Auriculares G535" -ForegroundColor Green
    Write-Host "[2] 🎮 Micro G535 → CABLE (Discord)" -ForegroundColor Blue
    Write-Host "[3] 🔊 Micro G535 → Altavoces PC" -ForegroundColor Magenta
    Write-Host "[4] 🎯 Discord Anti-Bucles (Recomendado)" -ForegroundColor Red
    Write-Host "[5] 📋 Ver dispositivos disponibles" -ForegroundColor White
    Write-Host "[6] ⚙️  Configuración manual" -ForegroundColor Gray
    Write-Host "[7] 🧪 Validar sistema" -ForegroundColor Cyan
    Write-Host "[8] 🎛️  Interfaz gráfica" -ForegroundColor Yellow
    Write-Host "[9] 🚪 Salir" -ForegroundColor Red
    Write-Host ""
}

function Start-Translation {
    param($InputId, $OutputId, $Description, $AntiLoop = $false)
    
    Write-Host ""
    Write-Host "🚀 Iniciando: $Description" -ForegroundColor Green
    Write-Host "📥 Entrada: Dispositivo $InputId" -ForegroundColor Cyan
    Write-Host "📤 Salida: Dispositivo $OutputId" -ForegroundColor Cyan
    
    if ($AntiLoop) {
        Write-Host ""
        Write-Host "🛡️  MODO ANTI-BUCLES ACTIVADO" -ForegroundColor Green
        Write-Host "✅ VAD Avanzado con supresión de ruido" -ForegroundColor Green
        Write-Host "✅ Detección de nivel de volumen (-30dB mínimo)" -ForegroundColor Green  
        Write-Host "✅ Puerta de ruido (-45dB)" -ForegroundColor Green
        Write-Host "✅ Cooldown de 500ms entre traducciones" -ForegroundColor Green
        Write-Host "✅ Máximo 3 traducciones consecutivas" -ForegroundColor Green
        Write-Host ""
        Write-Host "💡 IMPORTANTE: En Discord configura micrófono como 'CABLE Output'" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Red
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

function Test-System {
    Write-Host ""
    Write-Host "🧪 Ejecutando validación del sistema..." -ForegroundColor Cyan
    & .\.venv\Scripts\Activate.ps1
    python validate_system.py
    Write-Host ""
    Read-Host "Presiona Enter para continuar"
}

function Start-GUI {
    Write-Host ""
    Write-Host "🎛️  Iniciando interfaz gráfica..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
    python -m src.main
}

# Ejecución directa con parámetros
if ($Action -eq "direct") {
    Start-Translation -InputId $InputDevice -OutputId $OutputDevice -Description "Configuración personalizada"
    return
}

# Menú interactivo
while ($true) {
    Show-MainMenu
    $choice = Read-Host "Elige una opción (1-9)"
    
    switch ($choice) {
        1 { 
            Start-Translation -InputId 8 -OutputId 11 -Description "Micro G535 → Auriculares G535"
            break
        }
        2 { 
            Start-Translation -InputId 8 -OutputId 6 -Description "Micro G535 → CABLE (Discord)"
            break
        }
        3 { 
            Start-Translation -InputId 8 -OutputId 13 -Description "Micro G535 → Altavoces PC"
            break
        }
        4 {
            Start-Translation -InputId 13 -OutputId 40 -Description "Discord Anti-Bucles" -AntiLoop $true
            break
        }
        5 { 
            Show-Devices
        }
        6 {
            Write-Host ""
            $customInput = Read-Host "ID del dispositivo de entrada"
            $customOutput = Read-Host "ID del dispositivo de salida"
            Start-Translation -InputId $customInput -OutputId $customOutput -Description "Configuración manual"
            break
        }
        7 {
            Test-System
        }
        8 {
            Start-GUI
            break
        }
        9 { 
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
