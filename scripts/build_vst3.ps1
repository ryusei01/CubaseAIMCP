$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$TapDir = Join-Path $Root "vst3_audio_tap"
$BuildDir = Join-Path $TapDir "build"

$Cmake = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Kitware.CMake*" -Filter "cmake.exe" -Recurse -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $Cmake) {
    $Cmake = "C:\Program Files\CMake\bin\cmake.exe"
}
if (-not (Test-Path $Cmake)) {
    throw "cmake.exe not found. Install Kitware.CMake via winget."
}

New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

& $Cmake -S $TapDir -B $BuildDir -G "Visual Studio 17 2022" -A x64 `
    -DSMTG_ENABLE_VST3_PLUGIN_EXAMPLES=OFF `
    -DSMTG_ENABLE_VST3_HOSTING_EXAMPLES=OFF `
    -DSMTG_ENABLE_VSTGUI_SUPPORT=OFF
if ($LASTEXITCODE -ne 0) { throw "CMake configure failed" }

# Symlink post-step may fail without Developer Mode; plugin binary can still succeed.
& $Cmake --build $BuildDir --config Release --target CubaseAiAudioTap
$Built = Join-Path $BuildDir "VST3\Release\CubaseAiAudioTap.vst3"
if (-not (Test-Path $Built)) {
    throw "Built .vst3 bundle not found at $Built"
}

$Destinations = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Common\VST3\CubaseAiAudioTap.vst3"),
    (Join-Path $env:COMMONPROGRAMFILES "VST3\CubaseAiAudioTap.vst3")
)

foreach ($Dest in $Destinations) {
    New-Item -ItemType Directory -Force -Path (Split-Path $Dest) | Out-Null
    if (Test-Path $Dest) {
        Remove-Item -Recurse -Force $Dest
    }
    Copy-Item -Recurse -Force $Built $Dest
    Write-Host "Installed: $Dest"
}

Write-Host ""
Write-Host "Next in Cubase:"
Write-Host "  1. Restart Cubase or rescan plugins"
Write-Host "  2. F3 -> Stereo Out Insert -> add 'Cubase AI Audio Tap'"
Write-Host "  3. Play and run: python tap_reader.py"
