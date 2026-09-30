$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptRoot

Set-Location $repoRoot

Write-Host 'Installing build dependencies...'
python -m pip install --upgrade pip
python -m pip install -e .[build]

if ($LASTEXITCODE -ne 0) {
	exit $LASTEXITCODE
}

Write-Host 'Building MonacoShuffler.exe...'
python -m PyInstaller --noconfirm --onefile --windowed --name MonacoShuffler src/monaco_shuffler/main.py

if ($LASTEXITCODE -ne 0) {
	exit $LASTEXITCODE
}

Write-Host "Build complete. Find the executable in: $repoRoot\dist\MonacoShuffler.exe"