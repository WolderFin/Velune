param(
    [Parameter(Mandatory=$true)][string]$CertificateThumbprint,
    [string]$TimestampUrl = 'http://timestamp.digicert.com'
)
$ErrorActionPreference = 'Stop'
$exe = Join-Path $PSScriptRoot '..\dist\Velune.exe'
if (-not (Test-Path -LiteralPath $exe)) { throw 'Сначала соберите dist\Velune.exe' }
$signTool = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\bin' -Filter signtool.exe -Recurse |
    Where-Object FullName -Match '\\x64\\signtool\.exe$' |
    Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $signTool) { throw 'SignTool не найден. Установите Windows SDK.' }
& $signTool sign /sha1 $CertificateThumbprint /fd SHA256 /tr $TimestampUrl /td SHA256 /d Velune /du 'https://github.com/WolderFin/Velune' $exe
if ($LASTEXITCODE -ne 0) { throw 'Не удалось подписать Velune.exe' }
& $signTool verify /pa /all /v $exe
if ($LASTEXITCODE -ne 0) { throw 'Проверка подписи завершилась ошибкой' }
Write-Host 'Velune.exe подписан. Теперь заново запустите scripts/package_release.py и scripts/write_checksums.py.'
