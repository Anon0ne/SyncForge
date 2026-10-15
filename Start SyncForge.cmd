@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-rclone.ps1"
if errorlevel 1 (
    pause
    exit /b 1
)
set "PATH=%LOCALAPPDATA%\Programs\rclone;%PATH%"
if exist "%~dp0SyncForge.exe" (
    start "" "%~dp0SyncForge.exe"
) else (
    python app.py
    if errorlevel 1 pause
)
