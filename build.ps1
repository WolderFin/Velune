param([string]$Python = "$PSScriptRoot\.venv\Scripts\python.exe")
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & $Python -m PyInstaller --noconfirm Velune.spec
    if ($LASTEXITCODE -ne 0) { throw 'Failed to build Velune.exe' }
    & $Python scripts/package_release.py
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create the release archive' }
    & $Python scripts/package_source.py
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create the source archive' }
    & $Python scripts/write_checksums.py
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create checksums' }
    Write-Host "Ready: $PSScriptRoot\dist\Velune.exe"
} finally { Pop-Location }
