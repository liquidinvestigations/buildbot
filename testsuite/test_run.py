from time import time, sleep
import subprocess
import random
from contextlib import closing
from urllib.request import urlopen
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


def random_port():
    return random.randint(1025, 65535)


def http_get(url):
    with closing(urlopen(url)) as resp:
        return resp.read()


def test_tcp(factory, shared):
    host_port = random_port()
    write(shared / 'app', TCP_APP)
    write(shared / 'foo.txt', '-- bar --')

    argv = [
        'run',
        '--share', '{}:/mnt/shared'.format(shared),
        '--tcp', '{}:8000'.format(host_port),
        '/mnt/shared/app',
    ]

    with thread(lambda: factory.main(argv)):
        t0 = time()
        timeout = 120

        while time() < t0 + timeout:
            if (shared / 'up.txt').is_file():
                break
            sleep(.5)

        else:
            raise RuntimeError('app is not up after %d seconds' % timeout)

        resp = http_get('http://localhost:{}/foo.txt'.format(host_port))
        assert resp == b'-- bar --'

    assert (shared / 'done.txt').is_file()


def test_login(factory, shared):
    LOGIN_COMMANDS = b'sudo /mnt/shared/app\necho huzzah\nexit\n'

    host_port = random_port()
    write(shared / 'app', TCP_APP)
    write(shared / 'foo.txt', '-- bar --')
    result = None

    def login():
        import factory as factory_module  # noqa

        def invoke_ssh(command):
            nonlocal result
            result = subprocess.run(
                command,
                input=LOGIN_COMMANDS,
                stdout=subprocess.PIPE,
                timeout=120,
                check=True,
            )

        with monkeypatcher() as mocks:
            mocks.setattr(
                factory_module.VM,
                'invoke_ssh',
                staticmethod(invoke_ssh),
            )

            argv = [
                'login',
                '--share', '{}:/mnt/shared'.format(shared),
                '--tcp', '{}:8000'.format(host_port),
            ]

            factory_module.main(argv)

    with thread(login):
        t0 = time()
        timeout = 120

        while time() < t0 + timeout:
            if (shared / 'up.txt').is_file():
                break
            sleep(.5)

        else:
            raise RuntimeError('app is not up after %d seconds' % timeout)

        resp = http_get('http://localhost:{}/foo.txt'.format(host_port))
        assert resp == b'-- bar --'

    assert (shared / 'done.txt').is_file()
    assert b'huzzah' in result.stdout


def test_memory(factory):
    factory.main(['run', '-m', '800', '--swap', '300M', 'free', '-m'])

    output = factory.ssh_result.stdout.decode('latin1')
    values = {}
    for line in output.splitlines()[1:]:
        label, value = line.split()[:2]
        values[label] = int(value)

    assert 750 < values['Mem:'] <= 800
    assert 290 < values['Swap:'] <= 300


def test_cpus(factory):
    factory.main(['run', '-s', '3', 'grep', 'processor', '/proc/cpuinfo'])
    output = factory.ssh_result.stdout.decode('latin1')
    assert len(output.splitlines()) == 3
