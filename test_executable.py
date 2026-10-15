"""Integration smoke test for the built Windows app using isolated temp data."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

import app


def main():
    executable = Path('dist/SyncForge.exe').resolve()
    assert executable.is_file(), 'Build SyncForge.exe first.'
    rclone = app.rclone_executable()
    with tempfile.TemporaryDirectory(prefix='SyncForge-test-') as temporary:
        root = Path(temporary)
        source, destination = root / 'source', root / 'destination'
        source.mkdir()
        (source / 'document.txt').write_text('original', encoding='utf-8')
        (source / 'excluded.tmp').write_text('skip', encoding='utf-8')
        job = dict(id='smoke-test', name='Isolated integration test', mode='copy',
                   source=str(source), destination=str(destination),
                   excludes='*.tmp', versions=str(root / 'versions'))
        data = root / 'appdata' / 'SyncForge'
        data.mkdir(parents=True)
        jobs = data / 'jobs.json'
        jobs.write_text(json.dumps([job]), encoding='utf-8')
        environment = dict(os.environ, LOCALAPPDATA=str(root / 'appdata'))
        environment['PATH'] = str(Path(rclone).parent) + os.pathsep + environment.get('PATH', '')

        def run_job():
            result = subprocess.run([str(executable), '--run-job', job['id']],
                                    env=environment, timeout=60)
            assert result.returncode == 0, (data / 'smoke-test.log').read_text()

        run_job()
        assert (destination / 'document.txt').read_text() == 'original'
        assert not (destination / 'excluded.tmp').exists()
        print('PASS: packaged job runner copies files and applies exclusions')
        (source / 'document.txt').write_text('updated content with different size', encoding='utf-8')
        (destination / 'destination-only.txt').write_text('keep', encoding='utf-8')
        run_job()
        assert (destination / 'document.txt').read_text() == 'updated content with different size'
        assert (destination / 'destination-only.txt').exists()
        assert any(p.read_text() == 'original' for p in (root / 'versions').rglob('document.txt'))
        assert 'Started' in (data / 'smoke-test.log').read_text()
        print('PASS: updates, older versions, backup preservation, and job logs')
        job['mode'] = 'sync'
        jobs.write_text(json.dumps([job]), encoding='utf-8')
        run_job()
        assert not (destination / 'destination-only.txt').exists()
        print('PASS: explicit mirror removes destination extras')
        process = subprocess.Popen([str(executable)], env=environment)
        try:
            time.sleep(4)
            assert process.poll() is None, 'GUI exited during startup'
            print('PASS: packaged GUI stays running after startup')
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=15)


if __name__ == '__main__':
    main()
