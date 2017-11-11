#!/usr/bin/env python3

import os
import json
from pathlib import Path
import socket
import shutil
from tempfile import TemporaryDirectory
from subprocess import run, check_output
from contextlib import contextmanager
from argparse import ArgumentParser, REMAINDER
import shlex

"""
reference:
* http://kitchen.ci
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
* http://ubuntu-smoser.blogspot.ro/2013/02/using-ubuntu-cloud-images-without-cloud.html
"""

repo = Path(__file__).resolve().parent
SHARED = repo / 'shared'
IMAGES = repo / 'images'
VAR = repo / 'var'
QEMU_HACKED_ARM = repo / 'qemu-hacked-arm'


def get_arch():
    return check_output(['uname', '-m']).decode('latin1').strip()

def echo_run(cmd):
    print('+', *cmd)
    run(cmd, check=True)

@contextmanager
def cd(path):
    prev = os.getcwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(prev)

def kill_qemu_via_qmp(qmp_path):
    qmp = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    qmp.connect(qmp_path)
    # https://wiki.qemu.org/Documentation/QMP
    qmp.sendall(b'{"execute": "qmp_capabilities"}\n')
    qmp.sendall(b'{"execute": "quit"}\n')
    qmp.close()

@contextmanager
def instance(platform, shares, memory, smp, tcp, udp):
    platform_home = IMAGES / platform

    config_json = platform_home / 'config.json'
    if config_json.is_file():
        with config_json.open(encoding='utf8') as f:
            config = json.load(f)
    else:
        config = {}

    if not VAR.is_dir():
        VAR.mkdir()

    with TemporaryDirectory(prefix='kitchen-', dir=str(VAR)) as tmp_name:
        tmp = Path(tmp_name)

        def _share(s):
            (path, mountpoint) = s.split(':')
            return {
                'path': str(Path(path).resolve()),
                'mountpoint': mountpoint,
            }

        local_disk = tmp / 'local-disk.img'
        echo_run([
            'qemu-img', 'create',
            '-f', 'qcow2',
            '-b', str(platform_home / 'disk.img'),
            str(local_disk),
        ])

        login = config.get('login', {
            'username': 'ubuntu',
            'password': 'ubuntu',
        })

        netdev_arg = (
            'user,id=user,net=192.168.1.0/24,hostname=%h'
            ',hostfwd=tcp:127.0.0.1:%p-:22' # kitchen's ssh port
            + ''.join(
                ',hostfwd=tcp:127.0.0.1:{}-:{}'.format(*spec.split(':'))
                for spec in tcp
            )
            + ''.join(
                ',hostfwd=udp:127.0.0.1:{}-:{}'.format(*spec.split(':'))
                for spec in udp
            )
        )

        platform = {
            'name': 'factory',
            'driver': {
                'image': [{'file': str(local_disk), 'snapshot': 'off'}],
                'memory': memory,
                'networks': [{
                    'netdev': netdev_arg,
                    'device': 'virtio-net-pci,netdev=user',
                }],
                'cpus': smp,
                'username': login['username'],
                'password': login['password'],
                'hostshares': [_share(s) for s in shares],
            },
        }

        if get_arch() == 'aarch64':
            platform['driver']['bios'] = str(platform_home / 'arm-bios.fd')
            platform['driver']['binary'] = str(QEMU_HACKED_ARM)

        kitchen_yml = {
            'driver': {'name': 'qemu'},
            'platforms': [platform],
            'suites': [{'name': 'vm'}],
        }

        with (tmp / '.kitchen.yml').open('w', encoding='utf8') as f:
            print(json.dumps(kitchen_yml, indent=2), file=f)

        with cd(tmp):
            try:
                try:
                    echo_run(['kitchen', 'create'])
                    yield
                finally:
                    kill_qemu_via_qmp('.kitchen/vm-factory.qmp')

            except:
                echo_run(['cat', '.kitchen/logs/kitchen.log'])
                raise

def run_factory(platform, *args):
    parser = ArgumentParser()
    parser.add_argument('--share', action='append', default=[])
    parser.add_argument('-m', '--memory', default=512, type=int)
    parser.add_argument('-p', '--smp', default=1, type=int)
    parser.add_argument('args', nargs=REMAINDER)
    parser.add_argument('--tcp', action='append', default=[])
    parser.add_argument('--udp', action='append', default=[])
    options = parser.parse_args(args)

    with instance(platform, options.share, options.memory, options.smp, options.tcp, options.udp):
        args = ['sudo'] + options.args
        cmd = ' '.join(shlex.quote(a) for a in args)
        echo_run(['kitchen', 'exec', '-c', cmd])

def login(platform, *args):
    parser = ArgumentParser()
    parser.add_argument('--share', action='append', default=[])
    parser.add_argument('-m', '--memory', default=512, type=int)
    parser.add_argument('-p', '--smp', default=1, type=int)
    parser.add_argument('--tcp', action='append', default=[])
    parser.add_argument('--udp', action='append', default=[])
    options = parser.parse_args(args)
    with instance(platform, options.share, options.memory, options.smp, options.tcp, options.udp):
        echo_run(['kitchen', 'login'])

CLOUD_INIT_YML = """\
#cloud-config
password: ubuntu
chpasswd: { expire: False }
ssh_pwauth: True
runcmd:
  - "dd if=/dev/zero of=/var/local/swap1 bs=1M count=2048"
  - "mkswap /var/local/swap1"
  - "echo '/var/local/swap1 none swap sw 0 0' >> /etc/fstab"
  - "touch /etc/cloud/cloud-init.disabled"
  - "systemctl disable apt-daily.service"
  - "systemctl disable apt-daily.timer"
  - "poweroff"
"""

def download_if_missing(path, url):
    if not path.is_file():
        echo_run(['wget', url, '-O', str(path), '-q'])

class BaseBuilder:

    def __init__(self, db_root, workbench):
        self.workbench = workbench
        self.db = db_root / self.name
        self.db.mkdir(exist_ok=True)
        self.disk = self.workbench / 'disk.img'
        upstream_image_name = self.upstream_image_url.rsplit('/', 1)[-1]
        self.upstream_image = self.db / upstream_image_name

    def download(self):
        download_if_missing(self.upstream_image, self.upstream_image_url)

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

    upstream_image_url = (
        'https://cloud-images.ubuntu.com/server/releases/16.04/release/'
        'ubuntu-16.04-server-cloudimg-amd64-disk1.img'
    )

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

    upstream_image_url = (
        'https://cloud-images.ubuntu.com/server/releases/16.04/release/'
        'ubuntu-16.04-server-cloudimg-arm64-uefi1.img'
    )

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
    options = parser.parse_args(args)

    print("Preparing factory image for", platform)
    builder_cls = PLATFORMS[platform]

    db_root = Path(options.db)
    db_root.mkdir(exist_ok=True)

    workbench = Path(__file__).resolve().parent / 'images' / platform
    workbench.mkdir()
    try:
        builder_cls(db_root, workbench).build()
    except:
        shutil.rmtree(str(workbench))
        raise

COMMANDS = {
    'run': run_factory,
    'login': login,
    'prepare-cloud-image': prepare_cloud_image,
}

DEFAULTS = {
    'x86_64': 'cloud-x86_64',
    'aarch64': 'cloud-arm64',
}


def main():
    arch = get_arch()
    if arch in DEFAULTS.keys():
        default_platform = DEFAULTS[arch]
    else:
        raise RuntimeError("Architecture {} not supported.".format(arch))

    platform_list = [x.name for x in IMAGES.iterdir() if x.is_dir()]

    parser = ArgumentParser()
    parser.add_argument('--platform',
                        choices=platform_list,
                        default=default_platform)
    parser.add_argument('command', choices=COMMANDS.keys())
    (options, args) = parser.parse_known_args()
    COMMANDS[options.command](options.platform, *args)
