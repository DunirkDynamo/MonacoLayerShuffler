$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptRoot
$srcRoot = Join-Path $repoRoot 'src'

Set-Location $repoRoot

$existingPythonPath = $env:PYTHONPATH
if ([string]::IsNullOrWhiteSpace($existingPythonPath)) {
    $env:PYTHONPATH = $srcRoot
}
else {
    $env:PYTHONPATH = "$srcRoot;$existingPythonPath"
}

Write-Host 'Launching Monaco Shuffler from source...'
python -m monaco_shuffler.main @args