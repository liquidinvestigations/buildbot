from time import time, sleep
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from pathlib import Path
import threading
import subprocess


def write(path, content, mode=0o755):
    with path.open('w', encoding='utf8') as f:
        f.write(content)
    path.chmod(mode)


def test_run_touch(factory):
    with TemporaryDirectory() as shared:
        factory.main([
            'run',
            '--share', '{}:/mnt/shared'.format(shared),
            'touch', '/mnt/shared/world.txt',
        ])
        assert (Path(shared) / 'world.txt').is_file()


TCP_APP = '''\
#!/usr/bin/env python3

import os
from pathlib import Path
import socketserver
from http.server import SimpleHTTPRequestHandler as Handler

os.chdir('/mnt/shared')

httpd = socketserver.TCPServer(('0.0.0.0', 8000), Handler)

Path('up.txt').touch()
httpd.handle_request()

Path('done.txt').touch()
'''


@contextmanager
def factory_thread(target):
    thread = threading.Thread(target=target)
    thread.start()
    yield
    thread.join()


def http_get(url):
    return subprocess.check_output(['curl', url])


def test_tcp(factory):
    with TemporaryDirectory() as shared:
        shared = Path(shared)
        write(shared / 'app', TCP_APP)
        write(shared / 'foo.txt', '-- bar --')

        argv = [
            'run',
            '--share', '{}:/mnt/shared'.format(shared),
            '--tcp', '42657:8000',
            '/mnt/shared/app',
        ]

        with factory_thread(lambda: factory.main(argv)):
            t0 = time()
            timeout = 20

            while time() < t0 + timeout:
                if (shared / 'up.txt').is_file():
                    break
                sleep(.5)

            else:
                raise RuntimeError('app is not up after %d seconds' % timeout)

            assert http_get('http://localhost:42657/foo.txt') == b'-- bar --'

        assert (shared / 'done.txt').is_file()
