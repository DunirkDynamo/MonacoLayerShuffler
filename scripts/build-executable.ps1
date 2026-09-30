$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptRoot

Set-Location $repoRoot

Write-Host 'Installing build dependencies...'
python -m pip install --upgrade pip
python -m pip install -e .[build]

Write-Host 'Building MonacoShuffler.exe...'
python -m PyInstaller --noconfirm --onefile --windowed --name MonacoShuffler -m monaco_shuffler.main

Write-Host "Build complete. Find the executable in: $repoRoot\dist\MonacoShuffler.exe"