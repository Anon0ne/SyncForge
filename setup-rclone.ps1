$ErrorActionPreference = 'Stop'
try {
    $installDir = Join-Path $env:LOCALAPPDATA 'Programs\rclone'
    $rclonePath = Join-Path $installDir 'rclone.exe'
    $existing = Get-Command rclone.exe -ErrorAction SilentlyContinue
    if ($existing) {
        $rclonePath = $existing.Source
        $installDir = Split-Path -Parent $rclonePath
    }
    if (-not (Test-Path -LiteralPath $rclonePath)) {
        Write-Host 'Installing rclone from downloads.rclone.org...'
        $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
        $platform = switch ($arch) { 'Arm64' { 'arm64' } 'X86' { '386' } default { 'amd64' } }
        $stagingDir = Join-Path $env:TEMP ('RcloneDesk-' + [guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $stagingDir | Out-Null
        $archive = Join-Path $stagingDir 'rclone.zip'
        Invoke-WebRequest -Uri "https://downloads.rclone.org/rclone-current-windows-$platform.zip" -OutFile $archive
        Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $stagingDir 'extracted')
        $binary = Get-ChildItem -LiteralPath (Join-Path $stagingDir 'extracted') -Filter rclone.exe -Recurse | Select-Object -First 1
        if (-not $binary) { throw 'Download contains no rclone.exe.' }
        & $binary.FullName version
        if ($LASTEXITCODE -ne 0) { throw 'Downloaded rclone could not run.' }
        New-Item -ItemType Directory -Path $installDir -Force | Out-Null
        Copy-Item -LiteralPath $binary.FullName -Destination $rclonePath -Force
    }
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $entries = @($userPath -split ';' | Where-Object { $_ })
    if ($entries -notcontains $installDir) {
        [Environment]::SetEnvironmentVariable('Path', (($entries + $installDir) -join ';'), 'User')
    }
    & $rclonePath version
    if ($LASTEXITCODE -ne 0) { throw 'rclone verification failed.' }
    Write-Host 'rclone is ready.'
} catch {
    Write-Host "rclone setup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Check your internet connection and run the launcher again.'
    exit 1
}
