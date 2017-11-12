from time import time, sleep
import subprocess
from conftest import thread, monkeypatcher


def write(path, content, mode=0o755):
    with path.open('w', encoding='utf8') as f:
        f.write(content)
    path.chmod(mode)


def test_touch(factory, shared):
    factory.main([
        'run',
        '--share', '{}:/mnt/shared'.format(shared),
        'touch', '/mnt/shared/world.txt',
    ])
    assert (shared / 'world.txt').is_file()


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


def http_get(url):
    return subprocess.check_output(['curl', url])


def test_tcp(factory, shared):
    write(shared / 'app', TCP_APP)
    write(shared / 'foo.txt', '-- bar --')

    argv = [
        'run',
        '--share', '{}:/mnt/shared'.format(shared),
        '--tcp', '42657:8000',
        '/mnt/shared/app',
    ]

    with thread(lambda: factory.main(argv)):
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


def test_login(factory, shared):
    LOGIN_COMMANDS = b'sudo /mnt/shared/app\necho huzzah\nexit\n'

    write(shared / 'app', TCP_APP)
    write(shared / 'foo.txt', '-- bar --')
    result = None

    def login():
        import factory as factory_module  # noqa

        def patched_vm_login():
            nonlocal result
            result = subprocess.run(
                ['kitchen', 'login'],
                input=LOGIN_COMMANDS,
                stdout=subprocess.PIPE,
                timeout=60,
                check=True,
            )

        with monkeypatcher() as mocks:
            mocks.setattr(factory_module, 'vm_login', patched_vm_login)

            argv = [
                'login',
                '--share', '{}:/mnt/shared'.format(shared),
                '--tcp', '42657:8000',
            ]

            factory_module.main(argv)

    with thread(login):
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
    assert b'huzzah' in result.stdout
