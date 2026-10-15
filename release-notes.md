SyncForge 0.1b Terminal Update refreshes the Windows GUI with a retro terminal theme.

![SyncForge terminal GUI](https://raw.githubusercontent.com/Anon0ne/SyncForge/v0.1b-terminal/assets/syncforge-terminal.png)

New: phosphor-green text, amber accents, monospace typography, square panes,
bracketed controls, and inverted hover states. Inspired by the Terminal CLI
preset at https://www.designprompts.dev/terminal.

**Downloads:** use the Windows ZIP for automatic rclone setup. The standalone
SyncForge.exe includes Python but requires rclone to be installed already.

**Validation:** compiled EXE tested with temporary files for copy, exclusions,
updates, version preservation, backup preservation, mirror deletion, job logs,
and GUI startup. Cloud transfers and Task Scheduler execution remain untested.

Download the Windows ZIP, extract it, and run **Start SyncForge.cmd**. The launcher
sets up rclone automatically. The packaged app includes Python; source users need
Python 3 with Tkinter.

Includes saved jobs, backup/mirror modes, dry-run previews, exclusions, version
folders, live logs, cancellation, and daily schedules.

This beta is unsigned. Remote configuration uses rclone's console wizard, and
remote paths are typed manually. See README.md for scheduling and backup limits.
