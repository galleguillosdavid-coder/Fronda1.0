# ====================================================================
#   SCRIPT DE OPTIMIZACION GRAFICA INTEGRAL - WINDOWS 11
#   Hardware: Intel Iris Plus Graphics (Ice Lake 10th Gen)
# ====================================================================

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " [>>] INICIANDO OPTIMIZACION DEL SUBSISTEMA GRAFICO" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Optimizacion de Modo Juego y GameDVR
Write-Host "`n[1/5] Configurando Windows Game Mode y latencia de video..." -ForegroundColor Yellow

$gameBarKey = "HKCU:\Software\Microsoft\GameBar"
if (-not (Test-Path $gameBarKey)) { New-Item -Path $gameBarKey -Force | Out-Null }
Set-ItemProperty -Path $gameBarKey -Name "AllowAutoGameMode" -Value 1 -Type DWord -Force
Set-ItemProperty -Path $gameBarKey -Name "AutoGameModeEnabled" -Value 1 -Type DWord -Force

$gameConfigKey = "HKCU:\System\GameConfigStore"
if (-not (Test-Path $gameConfigKey)) { New-Item -Path $gameConfigKey -Force | Out-Null }
Set-ItemProperty -Path $gameConfigKey -Name "GameDVR_Enabled" -Value 0 -Type DWord -Force
Set-ItemProperty -Path $gameConfigKey -Name "GameDVR_FSEBehaviorMode" -Value 2 -Type DWord -Force
Set-ItemProperty -Path $gameConfigKey -Name "GameDVR_HonorUserFSEBehaviorMode" -Value 1 -Type DWord -Force
Set-ItemProperty -Path $gameConfigKey -Name "GameDVR_DXGIHonorFSEWindowsCompatible" -Value 1 -Type DWord -Force
Set-ItemProperty -Path $gameConfigKey -Name "GameDVR_EFSEFeatureFlags" -Value 0 -Type DWord -Force

Write-Host " [OK] Modo Juego activado y GameDVR en segundo plano desactivado." -ForegroundColor Green

# 2. Optimizaciones DirectX Flip Model
Write-Host "`n[2/5] Optimizando modelo de presentacion DirectX (Flip Model)..." -ForegroundColor Yellow

$directXPrefKey = "HKCU:\Software\Microsoft\DirectX\UserGpuPreferences"
if (-not (Test-Path $directXPrefKey)) { New-Item -Path $directXPrefKey -Force | Out-Null }
Set-ItemProperty -Path $directXPrefKey -Name "DirectXUserGlobalSettings" -Value "SwapEffectUpgradeEnable=1;" -Type String -Force

Write-Host " [OK] Modern Flip Model activado para renderizado de baja latencia." -ForegroundColor Green

# 3. Limpieza y Purga de Cache de Sombreadores
Write-Host "`n[3/5] Purgando cache de sombreadores DirectX e Intel..." -ForegroundColor Yellow

$d3dCache = "$env:LOCALAPPDATA\D3DSCache"
$intelCache = "$env:LOCALAPPDATA\Intel\ShaderCache"
$cleaned = 0

if (Test-Path $d3dCache) {
    $items = Get-ChildItem -Path "$d3dCache\*" -Recurse -Force -ErrorAction SilentlyContinue
    $cleaned += ($items | Measure-Object).Count
    Remove-Item -Path "$d3dCache\*" -Recurse -Force -ErrorAction SilentlyContinue
}

if (Test-Path $intelCache) {
    $items = Get-ChildItem -Path "$intelCache\*" -Recurse -Force -ErrorAction SilentlyContinue
    $cleaned += ($items | Measure-Object).Count
    Remove-Item -Path "$intelCache\*" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host " [OK] Cache de sombreadores purgada ($cleaned elementos liberados)." -ForegroundColor Green

# 4. Actualizacion del Perfil de PowerShell con 'sysgfx'
Write-Host "`n[4/5] Registrando funcion 'sysgfx' en el perfil de terminal..." -ForegroundColor Yellow

$fnCode = @"

# ---------------------------------------------------------
# Helper Grafico: sysgfx (Diagnostico y Mantenimiento de GPU)
# ---------------------------------------------------------
function sysgfx {
    [CmdletBinding()]
    param([switch]`$CleanCache)

    Write-Host "`n=== [ ESTADO DEL SUBSISTEMA GRAFICO ] ===" -ForegroundColor Cyan
    `$gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1
    `$res = "`$(`$gpu.CurrentHorizontalResolution)x`$(`$gpu.CurrentVerticalResolution) @ `$(`$gpu.CurrentRefreshRate)Hz"
    
    Write-Host " - Adaptador GPU:   " -NoNewline; Write-Host "`$(`$gpu.Name)" -ForegroundColor Green
    Write-Host " - Driver Version:  " -NoNewline; Write-Host "`$(`$gpu.DriverVersion) (`$(`$gpu.DriverDate))" -ForegroundColor Yellow
    Write-Host " - Pantalla Actual: " -NoNewline; Write-Host "`$res" -ForegroundColor White
    Write-Host " - Estado:          " -NoNewline; Write-Host "`$(`$gpu.Status)" -ForegroundColor Green

    if (`$CleanCache) {
        Write-Host "`nLimpiando Shader Cache..." -ForegroundColor Cyan
        Remove-Item "`$env:LOCALAPPDATA\D3DSCache\*" -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item "`$env:LOCALAPPDATA\Intel\ShaderCache\*" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Shader Cache DirectX / Intel reiniciada." -ForegroundColor Green
    }

    Write-Host "`nAtajos utiles:" -ForegroundColor DarkGray
    Write-Host " - Win + Ctrl + Shift + B : Reiniciar pipeline de video al vuelo." -ForegroundColor DarkGray
    Write-Host " - sysgfx -CleanCache     : Purgar shader cache de DirectX." -ForegroundColor DarkGray
    Write-Host "=========================================`n" -ForegroundColor Cyan
}
"@

$profilePaths = @(
    "$env:USERPROFILE\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1",
    "$env:USERPROFILE\Documents\PowerShell\Microsoft.PowerShell_profile.ps1"
)

foreach ($pPath in $profilePaths) {
    $dir = Split-Path $pPath -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    
    $currentContent = ""
    if (Test-Path $pPath) {
        $currentContent = Get-Content -Path $pPath -Raw -ErrorAction SilentlyContinue
    }
    
    if ($currentContent -notmatch "function sysgfx") {
        Add-Content -Path $pPath -Value "`n$fnCode" -Force
        Write-Host " [OK] Funcion 'sysgfx' agregada a: $(Split-Path $pPath -Leaf)" -ForegroundColor Green
    } else {
        Write-Host " [OK] Funcion 'sysgfx' ya presente en: $(Split-Path $pPath -Leaf)" -ForegroundColor Gray
    }
}

# 5. Resumen de Hardware
Write-Host "`n[5/5] Resumen de Hardware y Estado:" -ForegroundColor Yellow
$gpuInfo = Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, DriverDate, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate | Format-List | Out-String
Write-Host $gpuInfo -ForegroundColor White

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " [OK] OPTIMIZACION GRAFICA COMPLETADA CON EXITO" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
