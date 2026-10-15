# Changelog

## 0.1b Terminal Update

- Replaced default widget styling with a green-on-black terminal interface.
- Added amber accents, monospace typography, bracketed buttons, and square panes.
- Added an actual GUI screenshot to the README.
- Published a standalone Windows EXE alongside the launcher ZIP.
- Verified the compiled job runner with isolated backup, exclusion, versioning,
  mirror, log, and GUI startup checks (`python test_executable.py`).

## 0.1b

Initial public beta of SyncForge for Windows.

- Saved backup and mirror jobs powered by rclone.
- Dry-run previews, exclusions, live logs and cancellation.
- Optional older-version folders and daily Windows Task Scheduler jobs.
- Automatic rclone installation and user PATH setup in the launcher.
- SyncForge branding and Windows application icon.

Known limitations: remote setup opens rclone's console wizard; remote paths are
entered manually. Schedules require the account to be signed in and the PC awake.
No overlap prevention, automatic retention cleanup, or restore wizard yet.
