param([string]$Python = "$PSScriptRoot\.venv\Scripts\python.exe")
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & $Python -m PyInstaller --noconfirm Velune.spec
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось собрать Velune.exe' }
    & $Python scripts/package_release.py
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось создать архив релиза' }
    & $Python scripts/write_checksums.py
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось создать контрольные суммы' }
    Write-Host "Готово: $PSScriptRoot\dist\Velune.exe"
} finally { Pop-Location }
