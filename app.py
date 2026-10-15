"""SyncForge — Windows desktop backup manager powered by rclone."""
import datetime as dt
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

VERSION = '0.1b'
ASSETS = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets'
DATA = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'SyncForge'
LEGACY_DATA = DATA.parent / 'RcloneDesk'
JOBS = DATA / 'jobs.json'


def rclone_executable():
    """Use a portable local copy first, including from scheduled runs."""
    root = Path(__file__).resolve().parent
    candidates = [Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'Programs' / 'rclone' / 'rclone.exe',
                  root / 'rclone.exe', root / 'tools' / 'rclone.exe']
    candidates.extend(sorted((root / 'tools').glob('rclone-*/rclone.exe')))
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    installed = shutil.which('rclone')
    if installed:
        return installed
    raise FileNotFoundError(
        'rclone.exe is missing. Extract the Windows download from '
        'https://rclone.org/downloads/ and place rclone.exe beside app.py, '
        'then click Refresh connections.')


def read_jobs():
    if not JOBS.exists():
        legacy = LEGACY_DATA / 'jobs.json'
        if legacy.exists():
            return json.loads(legacy.read_text(encoding='utf-8'))
        return []
    return json.loads(JOBS.read_text(encoding='utf-8'))


def save_jobs(jobs):
    DATA.mkdir(parents=True, exist_ok=True)
    temporary = JOBS.with_suffix('.tmp')
    temporary.write_text(json.dumps(jobs, indent=2), encoding='utf-8')
    temporary.replace(JOBS)


def command(job, preview=False):
    source, destination = job['source'].strip(), job['destination'].strip()
    if not source or not destination or source.rstrip('/\\').casefold() == destination.rstrip('/\\').casefold():
        raise ValueError('Choose different, nonempty source and destination paths.')
    args = [rclone_executable(), job['mode'], source, destination,
            '--stats', '1s', '--stats-one-line', '--log-level', 'INFO']
    if preview:
        args.append('--dry-run')
    for pattern in job.get('excludes', '').splitlines():
        if pattern.strip():
            args.extend(['--exclude', pattern.strip()])
    if job.get('versions'):
        stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        args.extend(['--backup-dir', job['versions'].rstrip('/\\') + '/' + stamp])
    return args


def scheduled_run(job_id):
    job = next(j for j in read_jobs() if j['id'] == job_id)
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / (job_id + '.log')).open('a', encoding='utf-8') as log:
        log.write('\nStarted ' + dt.datetime.now().isoformat() + '\n')
        log.flush()
        return subprocess.call(command(job), stdout=log, stderr=subprocess.STDOUT)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'SyncForge {VERSION} • Windows Backup Manager')
        if (ASSETS / 'syncforge.ico').exists():
            self.iconbitmap(str(ASSETS / 'syncforge.ico'))
        self.geometry('1080x780')
        self.minsize(850, 650)
        self.jobs = read_jobs()
        self.process = None
        self.events = queue.Queue()
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TButton', padding=7)
        style.configure('TLabel', padding=3)
        header = ttk.Frame(self, padding=16)
        header.pack(fill='x')
        ttk.Label(header, text=f'SyncForge  {VERSION}', font=('Segoe UI', 24, 'bold')).pack(side='left')
        ttk.Button(header, text='Connect storage', command=self.configure_storage).pack(side='right')
        ttk.Button(header, text='Refresh connections', command=self.refresh_remotes).pack(side='right', padx=6)
        self.connections = ttk.Label(self, text='Checking rclone…', padding=12)
        self.connections.pack(fill='x')
        body = ttk.Frame(self, padding=12)
        body.pack(fill='both', expand=True)
        left = ttk.Frame(body)
        left.pack(side='left', fill='y', padx=(0, 16))
        ttk.Label(left, text='SAVED JOBS', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.list = tk.Listbox(left, width=25, exportselection=False)
        self.list.pack(fill='both', expand=True)
        self.list.bind('<<ListboxSelect>>', self.select_job)
        ttk.Button(left, text='+ New job', command=self.new_job).pack(fill='x', pady=6)
        right = ttk.Frame(body)
        right.pack(side='left', fill='both', expand=True)
        self.fields = {}
        for key, title in [('name', 'Job name'), ('source', 'Source — local folder or remote:path'),
                           ('destination', 'Destination — local folder or remote:path'),
                           ('versions', 'Optional older-version folder — outside destination')]:
            ttk.Label(right, text=title).pack(anchor='w')
            row = ttk.Frame(right)
            row.pack(fill='x')
            value = tk.StringVar()
            self.fields[key] = value
            ttk.Entry(row, textvariable=value).pack(side='left', fill='x', expand=True)
            if key != 'name':
                ttk.Button(row, text='Folder…', command=lambda v=value: self.choose_folder(v)).pack(side='right')
        self.mode = tk.StringVar(value='copy')
        modes = ttk.Frame(right, padding=(0, 8))
        modes.pack(fill='x')
        ttk.Radiobutton(modes, text='Backup (preserve destination files)', variable=self.mode, value='copy').pack(anchor='w')
        ttk.Radiobutton(modes, text='Mirror (delete destination extras)', variable=self.mode, value='sync').pack(anchor='w')
        ttk.Label(right, text='Exclude patterns — one per line, e.g. *.tmp').pack(anchor='w')
        self.excludes = tk.Text(right, height=3, font=('Consolas', 10))
        self.excludes.pack(fill='x')
        actions = ttk.Frame(right, padding=(0, 10))
        actions.pack(fill='x')
        for label, action in [('Save job', self.save), ('Preview', lambda: self.run(True)),
                              ('Run backup', lambda: self.run(False)), ('Cancel', self.cancel),
                              ('Schedule daily', self.schedule)]:
            ttk.Button(actions, text=label, command=action).pack(side='left', padx=2)
        self.status = ttk.Label(right, text='Ready. Preview a job before its first run.')
        self.status.pack(anchor='w')
        self.output = tk.Text(right, height=13, bg='#142031', fg='#dce8f5', font=('Consolas', 10), wrap='word')
        self.output.pack(fill='both', expand=True)
        self.current_id = None
        self.update_list()
        self.after(100, self.refresh_remotes)
        self.after(100, self.poll)
        self.protocol('WM_DELETE_WINDOW', self.close)

    def choose_folder(self, variable):
        path = filedialog.askdirectory()
        if path:
            variable.set(path)

    def configure_storage(self):
        try:
            subprocess.Popen([rclone_executable(), 'config'], creationflags=subprocess.CREATE_NEW_CONSOLE)
        except OSError as error:
            messagebox.showerror('Cannot open storage setup', str(error))

    def refresh_remotes(self):
        def worker():
            try:
                result = subprocess.run([rclone_executable(), 'listremotes'], capture_output=True, text=True, timeout=20,
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                text = 'Connected storage: ' + (', '.join(result.stdout.split()) or 'No remotes configured. Local and NAS folders are available.')
                if result.returncode:
                    text = result.stderr.strip()
            except (OSError, subprocess.TimeoutExpired) as error:
                text = str(error)
            self.events.put(('connections', text))
        threading.Thread(target=worker, daemon=True).start()

    def update_list(self):
        self.list.delete(0, 'end')
        for job in self.jobs:
            self.list.insert('end', job['name'])

    def new_job(self):
        self.current_id = None
        for value in self.fields.values():
            value.set('')
        self.mode.set('copy')
        self.excludes.delete('1.0', 'end')

    def select_job(self, _event):
        if not self.list.curselection():
            return
        job = self.jobs[self.list.curselection()[0]]
        self.current_id = job['id']
        for key, value in self.fields.items():
            value.set(job.get(key, ''))
        self.mode.set(job['mode'])
        self.excludes.delete('1.0', 'end')
        self.excludes.insert('1.0', job.get('excludes', ''))

    def job(self):
        import uuid
        job = {key: value.get().strip() for key, value in self.fields.items()}
        job.update(id=self.current_id or uuid.uuid4().hex, mode=self.mode.get(), excludes=self.excludes.get('1.0', 'end').strip())
        if not job['name']:
            raise ValueError('Give this job a name.')
        command(job)
        return job

    def save(self):
        try:
            job = self.job()
            updated = [j for j in self.jobs if j['id'] != job['id']] + [job]
            save_jobs(updated)
            self.jobs, self.current_id = updated, job['id']
            self.update_list()
            self.status.config(text='Job saved.')
            return job
        except (ValueError, OSError) as error:
            messagebox.showerror('Cannot save job', str(error))

    def run(self, preview):
        if self.process is not None:
            messagebox.showinfo('Transfer active', 'Wait for the current transfer or cancel it.')
            return
        try:
            job = self.job()
            args = command(job, preview)
            if not preview and job['mode'] == 'sync' and not messagebox.askyesno('Confirm mirror', 'Mirror can delete files at the destination. Continue?'):
                return
            self.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                            encoding='utf-8', errors='replace', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except (ValueError, OSError) as error:
            messagebox.showerror('Cannot start transfer', str(error))
            return
        process = self.process
        self.status.config(text='Preview running…' if preview else 'Backup running…')
        self.output.delete('1.0', 'end')
        def worker():
            for line in process.stdout:
                self.events.put(('log', line))
            self.events.put(('done', process.wait()))
        threading.Thread(target=worker, daemon=True).start()

    def cancel(self):
        if self.process is not None:
            self.process.terminate()
            self.status.config(text='Cancellation requested…')

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'log':
                    self.output.insert('end', value)
                    self.output.see('end')
                elif kind == 'connections':
                    self.connections.config(text=value)
                elif kind == 'done':
                    self.process = None
                    self.status.config(text='Completed successfully.' if value == 0 else f'Stopped with exit code {value}. See log.')
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def schedule(self):
        job = self.save()
        if not job:
            return
        if job['mode'] == 'sync' and not messagebox.askyesno('Scheduled mirror', 'This schedule will delete destination extras without prompting each time. Continue?'):
            return
        time = simpledialog.askstring('Daily schedule', 'Daily start time (24-hour HH:MM):', initialvalue='20:00')
        if not time:
            return
        try:
            dt.datetime.strptime(time, '%H:%M')
            runner = [sys.executable] if getattr(sys, 'frozen', False) else [sys.executable, str(Path(__file__).resolve())]
            task_command = subprocess.list2cmdline(runner + ['--run-job', job['id']])
            result = subprocess.run(['schtasks', '/Create', '/F', '/TN', 'SyncForge-' + job['id'], '/TR', task_command,
                                     '/SC', 'DAILY', '/ST', time], capture_output=True, text=True,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if result.returncode:
                raise ValueError(result.stderr or result.stdout)
            messagebox.showinfo('Schedule created', f'Daily at {time}, while your Windows account is signed in.\nThe app can be closed.\nLogs: {DATA}\nManage or remove it in Windows Task Scheduler.')
        except (ValueError, OSError) as error:
            messagebox.showerror('Cannot schedule', str(error))

    def close(self):
        if self.process is not None:
            if not messagebox.askyesno('Transfer active', 'Cancel the active transfer and close?'):
                return
            self.cancel()
        self.destroy()


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--run-job':
        sys.exit(scheduled_run(sys.argv[2]))
    App().mainloop()
