#!/usr/bin/env python3

import sys
import os
import pty
from time import time, sleep
import json
import random
from pathlib import Path
import socket
import shutil
from tempfile import TemporaryDirectory
import subprocess
from contextlib import contextmanager
from argparse import ArgumentParser, REMAINDER
import shlex
import logging
import signal

"""
reference:
* http://kitchen.ci
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
* http://ubuntu-smoser.blogspot.ro/2013/02/using-ubuntu-cloud-images-without-cloud.html
"""

SSH_PRIVKEY = '''\
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACDPUAQxsWJNjIyRzGt9FLdeuv7OtWJNYnk592l4wJ57zwAAAJDgnRRK4J0U
SgAAAAtzc2gtZWQyNTUxOQAAACDPUAQxsWJNjIyRzGt9FLdeuv7OtWJNYnk592l4wJ57zw
AAAEBAAQzlJCFP03EyDr5D6ssyBshQ+1dvDYaZFXqkasWEs89QBDGxYk2MjJHMa30Ut166
/s61Yk1ieTn3aXjAnnvPAAAACW1nYXhAdHVmYQECAwQ=
-----END OPENSSH PRIVATE KEY-----
'''

SSH_PUBKEY = ('ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIM9QBDG'
              'xYk2MjJHMa30Ut166/s61Yk1ieTn3aXjAnnvP factory')

logger = logging.getLogger('factory')


def print_progress(text):
    if logger.level <= logging.INFO:
        print(text, end='', flush=True, file=sys.stderr)


class Paths:

    def __init__(self, repo):
        self.IMAGES = repo / 'images'
        self.VAR = repo / 'var'


code_repo = Path(__file__).resolve().parent
paths = Paths(code_repo)


def get_arch():
    return subprocess.check_output(['uname', '-m']).decode('latin1').strip()

def echo_run(cmd):
    logger.debug('+ ' + ' '.join(cmd))
    subprocess.run(cmd, check=True)

@contextmanager
def cd(path):
    prev = os.getcwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(prev)


def open_qmp(qmp_path):
    qmp = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        qmp.connect(qmp_path)
    except ConnectionRefusedError:
        return None
    else:
        return qmp


def kill_qemu_via_qmp(qmp_path):
    qmp = open_qmp(qmp_path)

    if not qmp:
        # qemu already quit, great!
        return

    # https://wiki.qemu.org/Documentation/QMP
    qmp.sendall(b'{"execute": "qmp_capabilities"}\n')
    qmp.sendall(b'{"execute": "quit"}\n')
    qmp.close()


class PtyProcessError(RuntimeError):
    pass


@contextmanager
def pty_process(command):
    """
    Start subprocess in a new PTY. Helps with the interactive ssh password
    prompt.
    """

    (pid, fd) = pty.fork()
    if not pid:
        os.execv(command[0], command)

    try:
        yield fd

    finally:
        (_, exit_code) = os.waitpid(pid, 0)
        if exit_code != 0:
            raise PtyProcessError()


def pty_ssh(remote, port, password, command):
    ssh_args = [
        '/usr/bin/ssh', remote,
        '-p', str(port),
        '-o', 'NumberOfPasswordPrompts=1',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=known_hosts',
        '-o', 'ConnectTimeout=1',
        command,
    ]

    with pty_process(ssh_args) as fd:
        while True:
            try:
                output = os.read(fd, 1024)
            except:
                return

            if b'password:' in output.lower().strip():
                os.write(fd, password.encode('utf8') + b'\n')

        while True:
            try:
                print_progress('{}\n'.format(os.read(fd, 1024)))
            except:
                return


DEFAULT_LOGIN = {
    'username': 'ubuntu',
    'password': 'ubuntu',
}


@contextmanager
def instance(platform, options, use_ssh=True):
    vm = VM(platform, options, use_ssh)
    with vm.var_folder():
        with vm.boot():
            yield vm


class VM:

    def __init__(self, platform, options, use_ssh):
        self.platform_home = paths.IMAGES / (options.image or platform)
        self.options = options
        self.use_ssh = use_ssh
        self.verbose = options.verbose

        config_json = self.platform_home / 'config.json'
        if config_json.is_file():
            with config_json.open(encoding='utf8') as f:
                self.config = json.load(f)
        else:
            self.config = {}

        self.tcp_ports = [spec.split(':') for spec in self.options.tcp]
        self.udp_ports = [spec.split(':') for spec in self.options.udp]

        self.cdrom_paths = [Path(p).resolve() for p in self.options.cdrom]
        self.usb_storage_paths = [
            Path(p).resolve()
            for p in self.options.usb_storage
        ]

        if self.use_ssh:
            self.login = self.config.get('login', DEFAULT_LOGIN)
            self.remote = '{}@localhost'.format(self.login['username'])
            self.port = random.randint(1025, 65535)
            self.tcp_ports.append((self.port, 22))

            self.shares = []
            for i, s in enumerate(self.options.share):
                (path, mountpoint) = s.split(':')
                self.shares.append((i, Path(path).resolve(), mountpoint))

        else:
            assert not self.options.share

    def setup_var(self):
        with (self.var / 'id_ed25519').open('w', encoding='latin1') as f:
            f.write(SSH_PRIVKEY)
        (self.var / 'id_ed25519').chmod(0o600)

        self.local_disk = self.var / 'local-disk.img'
        subprocess.run([
            'qemu-img', 'create', '-q',
            '-f', 'qcow2',
            '-b', str(self.platform_home / 'disk.img'),
            str(self.local_disk),
        ], check=True)

    @contextmanager
    def var_folder(self):
        if not paths.VAR.is_dir():
            paths.VAR.mkdir()

        with TemporaryDirectory(prefix='vm-', dir=str(paths.VAR)) as var:
            self.var = Path(var)
            self.setup_var()
            yield

    def qemu_argv(self):
        arch = get_arch()
        qemu_binary = 'qemu-system-{}'.format(arch)

        yield from [
            qemu_binary,
            '-daemonize',
            '-display', 'none',
            '-chardev', 'socket,id=mon-qmp,path=vm.qmp,server,nowait',
            '-mon', 'chardev=mon-qmp,mode=control',
            '-serial', 'mon:unix:path=vm.mon,server,nowait',
            '-m', str(self.options.memory),
            '-enable-kvm',
            '-cpu', 'host',
            '-smp', 'cpus={}'.format(self.options.smp),
        ]

        if arch == 'aarch64':
            yield from [
                '-M', 'virt',
                '-bios', str(self.platform_home / 'arm-bios.fd'),
            ]

        netdev_arg = (
            'user,id=user,net=192.168.1.0/24,hostname=vm-factory'
            + ''.join(
                ',hostfwd=tcp:127.0.0.1:{}-:{}'.format(*pair)
                for pair in self.tcp_ports
            )
            + ''.join(
                ',hostfwd=udp:127.0.0.1:{}-:{}'.format(*pair)
                for pair in self.udp_ports
            )
        )

        yield from [
            '-netdev', netdev_arg,
            '-device', 'virtio-net-pci,netdev=user,romfile=',
        ]

        def disk_drive(path):
            return [
                '-drive',
                'if=virtio,discard=unmap,detect-zeroes=unmap,file={}'
                    .format(path),
            ]

        yield from disk_drive(self.var / 'local-disk.img')

        for path in self.cdrom_paths:
            yield from ['-drive', 'file={},media=cdrom'.format(path)]

        for n, path in enumerate(self.usb_storage_paths):
            yield from [
                '-device', 'usb-storage,drive=usb{}'.format(n),
                '-drive', 'if=none,id=usb{},format=raw,file={}'.format(n, path),
            ]

        if self.use_ssh:
            for i, path, _ in self.shares:
                yield from [
                    '-fsdev', 'local,id=fsdev{i},security_model=none,path={path}'
                        .format(i=i, path=path),
                    '-device', 'virtio-9p-pci,fsdev=fsdev{i},mount_tag=path{i}'
                        .format(i=i),
                ]

            if self.options.swap:
                swap_disk = str(self.var / 'swap.img')
                subprocess.run([
                    'qemu-img', 'create', '-q',
                    '-f', 'qcow2',
                    swap_disk,
                    self.options.swap,
                ], check=True)

                yield from disk_drive(swap_disk)

        if self.options.vnc:
            assert 5900 <= self.options.vnc <= 5999
            display = self.options.vnc - 5900
            yield from ['-display', 'vnc=localhost:{}'.format(display)]

        if self.options.sdl:
            yield from ['-display', 'sdl']

        yield from self.config.get('qemu-args', [])

    def vm_bootstrap_commands(self):
        yield from [
            'mkdir -p ~/.ssh',
            'echo "{}" >> ~/.ssh/authorized_keys'.format(SSH_PUBKEY),
            'chmod 700 ~/.ssh',
            'chmod 600 ~/.ssh/authorized_keys',
        ]

        for i, _, mountpoint in self.shares:
            quoted_mountpoint = shlex.quote(mountpoint)
            yield 'sudo mkdir -p {}'.format(quoted_mountpoint)
            yield (
                'sudo mount -t 9p -o trans=virtio path{} {} -oversion=9p2000.L'
                .format(i, quoted_mountpoint)
            )

        if self.options.swap:
            yield from [
                'sudo mkswap /dev/vdb',
                'sudo swapon /dev/vdb',
            ]

    def vm_bootstrap(self, timeout=180):
        if self.verbose:
            console_socat = subprocess.Popen([
                'socat', '-',
                str(self.var / 'vm.mon'),
            ])

        password = self.login['password']
        bootstrap = ' && '.join(self.vm_bootstrap_commands())
        t0 = time()
        while time() < t0 + timeout:
            try:
                print_progress('.')
                pty_ssh(self.remote, self.port, password, bootstrap)

            except PtyProcessError:
                sleep(1)
                continue

            else:
                print_progress(':)\n')
                return

        raise RuntimeError("VM not up after {} seconds".format(timeout))

    def wait_for_qemu_sockets(self, timeout=5):
        t0 = time()
        files = [self.var / name for name in ['vm.qmp', 'vm.mon']]

        while time() < t0 + timeout:
            if all(f.exists() for f in files):
                break
            sleep(.1)

        else:
            raise RuntimeError("VM did not create its sockets")

    def shutdown(self, timeout=60):
        if self.use_ssh:
            try:
                self.ssh('sudo poweroff')
            except:
                pass

        print_progress("Waiting for the VM to shut down ")
        t0 = time()
        while time() < t0 + timeout:
            if open_qmp('vm.qmp') is None:
                # the socket is dead, so the VM must have stopped
                print_progress('\n')
                return
            print_progress('.')
            sleep(.2)

        print_progress('\n')
        raise RuntimeError("VM did not shut down normally")

    def commit(self):
        echo_run(['qemu-img', 'commit', str(self.local_disk)])

    @contextmanager
    def boot(self):
        with cd(self.var):
            qemu = list(self.qemu_argv())
            logger.debug('+ ' + ' '.join(qemu))
            subprocess.Popen(qemu)

            self.wait_for_qemu_sockets()

            try:
                if self.use_ssh:
                    self.vm_bootstrap()

                yield

                if self.options.commit:
                    self.shutdown()

                    def confirm_commit():
                        text = input("Commit? [Y/n]: ")
                        return text.strip().lower() in ['', 'y']

                    if self.options.yes or confirm_commit():
                        self.commit()

                    else:
                        logger.info("Aborting commit")

            finally:
                kill_qemu_via_qmp('vm.qmp')

    @staticmethod
    def invoke_ssh(cmd):
        subprocess.run(cmd, check=True)

    @staticmethod
    def invoke_console(socket_path):
        subprocess.run(['socat', '-,cfmakeraw,escape=0xf', str(socket_path)])

    def ssh(self, cmd=None):
        ssh_command = [
            'ssh',
            self.remote,
            '-p', str(self.port),
            '-o', 'UserKnownHostsFile=known_hosts',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=30',
            '-o', 'IdentitiesOnly=yes',
            '-i', 'id_ed25519',
        ]

        if cmd:
            ssh_command.append(cmd)

        self.invoke_ssh(ssh_command)

    def console(self):
        self.invoke_console(self.var / 'vm.mon')


def add_vm_arguments(parser):
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-i', '--image')
    parser.add_argument('--share', action='append', default=[])
    parser.add_argument('-m', '--memory', default=512, type=int)
    parser.add_argument('-s', '--smp', default=1, type=int)
    parser.add_argument('--tcp', action='append', default=[])
    parser.add_argument('--udp', action='append', default=[])
    parser.add_argument('--vnc', type=int)
    parser.add_argument('--sdl', action='store_true')
    parser.add_argument('--cdrom', action='append', default=[])
    parser.add_argument('--usb-storage', action='append', default=[])
    parser.add_argument('--swap', default='2G')
    parser.add_argument('--commit', action='store_true')
    parser.add_argument('-y', '--yes', action='store_true')


def run_factory(platform, *args):
    parser = ArgumentParser()
    add_vm_arguments(parser)
    parser.add_argument('args', nargs=REMAINDER)
    options = parser.parse_args(args)

    with instance(platform, options) as vm:
        args = ['sudo'] + options.args
        cmd = ' '.join(shlex.quote(a) for a in args)
        vm.ssh(cmd)


def login(platform, *args):
    parser = ArgumentParser()
    add_vm_arguments(parser)
    options = parser.parse_args(args)

    with instance(platform, options) as vm:
        vm.ssh()


def console(platform, *args):
    parser = ArgumentParser()
    add_vm_arguments(parser)
    options = parser.parse_args(args)

    with instance(platform, options, use_ssh=False) as vm:
        vm.console()


def create_image(_, *args):
    parser = ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('--size', default='8G')
    options = parser.parse_args(args)
    image_dir = paths.IMAGES / options.image
    image_dir.mkdir()
    disk_img = image_dir / 'disk.img'
    echo_run([
        'qemu-img', 'create',
        '-f', 'qcow2',
        str(disk_img),
        options.size,
    ])


def export_image(_, *args):
    image_list = [x.name for x in paths.IMAGES.iterdir() if x.is_dir()]
    parser = ArgumentParser()
    parser.add_argument('image', choices=image_list)
    options = parser.parse_args(args)

    image_dir = paths.IMAGES / options.image

    with cd(image_dir):
        subprocess.run(['tar', 'c', '.'], check=True)


def import_image(_, *args):
    parser = ArgumentParser()
    parser.add_argument('image')
    options = parser.parse_args(args)

    image_dir = paths.IMAGES / options.image
    image_dir.mkdir()

    with cd(image_dir):
        subprocess.run(['tar', 'x'], check=True)


CLOUD_INIT_YML = """\
#cloud-config
password: ubuntu
chpasswd: { expire: False }
ssh_pwauth: True
runcmd:
  - "echo '127.0.1.1 ubuntu' >> /etc/hosts"
  - "touch /etc/cloud/cloud-init.disabled"
  - "systemctl disable apt-daily.service"
  - "systemctl disable apt-daily.timer"
  - "poweroff"
"""

def download_if_missing(path, url):
    if not path.is_file():
        echo_run(['wget', url, '-O', str(path), '-q'])

class BaseBuilder:

    def __init__(self, db_root, workbench, flavor):
        self.workbench = workbench
        self.flavor = flavor
        self.db = db_root / self.name
        self.db.mkdir(exist_ok=True)
        self.disk = self.workbench / 'disk.img'
        upstream_image_name = self.get_upstream_image_url().rsplit('/', 1)[-1]
        self.upstream_image = self.db / upstream_image_name

    def download(self):
        download_if_missing(self.upstream_image, self.get_upstream_image_url())

    def unpack_upstream(self):
        echo_run(['qemu-img', 'convert', '-O', 'qcow2',
                    str(self.upstream_image), str(self.disk)])

        echo_run(['qemu-img', 'resize', str(self.disk), '10G'])

    def create_cloud_init_image(self):
        self.cloud_init_yml = self.workbench / 'cloud-init.yml'
        self.cloud_init_img = self.workbench / 'cloud-init.img'
        with self.cloud_init_yml.open('w', encoding='utf8') as f:
            f.write(CLOUD_INIT_YML)

        echo_run([
            'cloud-localds',
            str(self.cloud_init_img),
            str(self.cloud_init_yml),
        ])

    def cleanup(self):
        self.cloud_init_img.unlink()
        self.cloud_init_yml.unlink()

    def build(self):
        self.download()
        self.unpack_upstream()
        self.create_cloud_init_image()
        self.run_qemu()
        self.cleanup()


class Builder_x86_64(BaseBuilder):

    name = 'cloud-x86_64'

    def get_upstream_image_url(self):
        if self.flavor == 'xenial':
            return (
                'https://cloud-images.ubuntu.com/xenial/current/'
                'xenial-server-cloudimg-amd64-disk1.img'
            )
        elif self.flavor == 'artful':
            return (
                'https://cloud-images.ubuntu.com/artful/current/'
                'artful-server-cloudimg-amd64.img'
            )
        else:
            raise RuntimeError("Unknown flavor {}".format(self.flavor))

    def run_qemu(self):
        echo_run([
            'qemu-system-x86_64',
            '-enable-kvm',
            '-nographic',
            '-m', '512',
            '-netdev', 'user,id=user',
            '-device', 'virtio-net-pci,netdev=user',
            '-drive', 'index=0,media=disk,file=' + str(self.disk),
            '-drive', 'index=1,media=disk,format=raw,file='
                + str(self.cloud_init_img),
        ])


class Builder_arm64(BaseBuilder):

    name = 'cloud-arm64'

    def get_upstream_image_url(self):
        if self.flavor == 'xenial':
            return (
                'https://cloud-images.ubuntu.com/xenial/current/'
                'xenial-server-cloudimg-arm64-uefi1.img'
            )
        elif self.flavor == 'artful':
            return (
                'https://cloud-images.ubuntu.com/artful/current/'
                'artful-server-cloudimg-arm64.img'
            )
        else:
            raise RuntimeError("Unknown flavor {}".format(self.flavor))

    bios_url = (
        'https://releases.linaro.org/components/kernel/uefi-linaro/15.12/'
        'release/qemu64/QEMU_EFI.fd'
    )

    def __init__(self, *args):
        super().__init__(*args)
        self.arm_bios_fd = self.workbench / 'arm-bios.fd'

    def download(self):
        download_if_missing(self.arm_bios_fd, self.bios_url)
        super().download()

    def run_qemu(self):
        echo_run([
            'qemu-system-aarch64',
            '-cpu', 'host',
            '-enable-kvm',
            '-nographic',
            '-m', '512',
            '-machine', 'virt',
            '-bios', str(self.arm_bios_fd),
            '-netdev', 'user,id=user',
            '-device', 'virtio-net-pci,netdev=user,romfile=',
            '-device', 'virtio-blk-device,drive=image',
            '-drive', 'if=none,id=image,file=' + str(self.disk),
            '-device', 'virtio-blk-device,drive=cloud-init',
            '-drive', 'if=none,id=cloud-init,format=raw,file='
                + str(self.cloud_init_img),
        ])

PLATFORMS = {
    'cloud-x86_64': Builder_x86_64,
    'cloud-arm64': Builder_arm64,
}

def prepare_cloud_image(platform, *args):
    parser = ArgumentParser()
    parser.add_argument('--db', default=str(Path.home() / '.factory'))
    parser.add_argument('--flavor', default='xenial')
    options = parser.parse_args(args)

    logger.info("Preparing factory image for %s", platform)
    builder_cls = PLATFORMS[platform]

    db_root = Path(options.db)
    db_root.mkdir(exist_ok=True)

    workbench = paths.IMAGES / platform
    workbench.mkdir()
    try:
        builder_cls(db_root, workbench, options.flavor).build()
    except:
        shutil.rmtree(str(workbench))
        raise

COMMANDS = {
    'run': run_factory,
    'login': login,
    'console': console,
    'prepare-cloud-image': prepare_cloud_image,
    'create': create_image,
    'export': export_image,
    'import': import_image,
}

DEFAULTS = {
    'x86_64': 'cloud-x86_64',
    'aarch64': 'cloud-arm64',
}


def set_up_logging(quiet, verbose):
    if verbose:
        log_level = logging.DEBUG

    elif quiet:
        log_level = logging.ERROR

    else:
        log_level = logging.INFO

    logger.setLevel(log_level)
    logging.basicConfig(level=log_level, format='%(message)s')


def handle_sigterm():
    def handler(*args):
        logger.debug("Caught SIGTERM, shutting down")
        sys.exit(1)

    signal.signal(signal.SIGTERM, handler)


def main(argv):
    arch = get_arch()
    if arch in DEFAULTS.keys():
        default_platform = DEFAULTS[arch]
    else:
        raise RuntimeError("Architecture {} not supported.".format(arch))

    platform_list = [x.name for x in paths.IMAGES.iterdir() if x.is_dir()]

    parser = ArgumentParser()
    parser.add_argument('-q', '--quiet', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--platform',
                        choices=platform_list,
                        default=default_platform)
    parser.add_argument('command', choices=COMMANDS.keys())
    (options, args) = parser.parse_known_args(argv)
    set_up_logging(options.quiet, options.verbose)
    COMMANDS[options.command](options.platform, *args)


def cmd():
    handle_sigterm()
    main(sys.argv[1:])
