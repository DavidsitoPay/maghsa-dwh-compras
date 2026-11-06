param([string]$Salida = (Join-Path $env:TEMP 'maghsa-infra'))
$ErrorActionPreference = 'Stop'
$raiz = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$carga = Join-Path $raiz 'lambda-carga'
$build = Join-Path $env:TEMP 'maghsa-carga-build'
$zip = Join-Path $Salida 'maghsa-carga.zip'
if (-not (Test-Path (Join-Path $carga 'requirements.txt'))) { throw 'Falta lambda-carga/requirements.txt' }
Remove-Item $build -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $build, (Join-Path $build 'sql'), $Salida | Out-Null
Copy-Item (Join-Path $carga '*.py') $build
Copy-Item (Join-Path $raiz 'athena\etl\*.sql'), (Join-Path $raiz 'athena\etl\orden.txt') (Join-Path $build 'sql')
python -m pip install -r (Join-Path $carga 'requirements.txt') --target $build --upgrade --quiet
if ($LASTEXITCODE -ne 0) { throw 'pip fallo' }
Remove-Item $zip -Force -ErrorAction SilentlyContinue
tar.exe -a -c -f $zip -C $build (Get-ChildItem $build -Name)
if ($LASTEXITCODE -ne 0) { throw 'tar fallo' }
Write-Output "Paquete: $zip"
