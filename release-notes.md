# SyncForge 0.1 Official

Windows desktop backup and synchronization powered by rclone.

![SyncForge terminal interface](https://raw.githubusercontent.com/Anon0ne/SyncForge/v0.1/assets/syncforge-terminal.png)

## Download and run

Download **SyncForge-0.1-windows-x64.zip**, extract it to a permanent folder, and
run **Start SyncForge.cmd**. The launcher installs rclone if needed and adds it
to your user PATH. Python is included.

**SyncForge.exe** is also available separately for systems with rclone installed.

## Included

- Green-on-black terminal interface with amber accents and monospace fonts.
- Saved backup and mirror jobs, previews, exclusions, and live logs.
- Transfer progress bar and scanning activity indicator.
- Older-version folders and daily Windows Task Scheduler jobs.
- SyncForge application icon and Windows taskbar identity.

## Validation and limits

Compiled EXE tested using temporary files for copying, exclusions, updates,
version preservation, destination preservation in backup mode, mirror deletion,
job logs, and GUI startup. Progress percentage and completion state also checked.
Cloud transfers and Task Scheduler execution have not been verified.

Remote setup uses rclone's console wizard; remote paths are entered manually.
Schedules require the account to be signed in and the computer awake. No overlap
prevention, retention cleanup, or restore wizard yet. The executable is unsigned.
