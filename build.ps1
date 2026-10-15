$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m PyInstaller --noconfirm --clean --onefile --windowed --name SyncForge --icon assets/syncforge.ico --add-data 'assets;assets' app.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }
$package = Join-Path $PSScriptRoot 'dist/SyncForge-0.1b-windows-x64'
New-Item -ItemType Directory -Path $package -Force | Out-Null
Copy-Item dist/SyncForge.exe $package
Copy-Item 'Start SyncForge.cmd', setup-rclone.ps1, README.md, CHANGELOG.md $package
Compress-Archive -Path "$package/*" -DestinationPath dist/SyncForge-0.1b-windows-x64.zip -Force
