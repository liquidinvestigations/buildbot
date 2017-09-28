#!/usr/bin/env python3

"""
Download Ubuntu cloud image and prepre it for use with Kitchen

reference:
* http://kitchen.ci
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
* http://ubuntu-smoser.blogspot.ro/2013/02/using-ubuntu-cloud-images-without-cloud.html
"""

import json
from pathlib import Path
import shutil
from subprocess import check_call, check_output
from argparse import ArgumentParser

def get_arch():
    return check_output(['uname', '-m']).decode('latin1').strip()


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

class BaseBuilder:

    base_image_url = None

    def __init__(self, images):
        self.images = images
        self.disk_img_orig = images / 'disk.img.orig'
        self.disk_img_dist = images / 'disk.img.dist'
        self.disk_img = images / 'disk.img'

    def download(self):
        self.images.mkdir(exist_ok=True)
        if not self.disk_img_orig.is_file():
            check_call([
                'wget', str(self.base_image_url),
                '-O', str(self.disk_img_dist),
                '-q'
            ])
            check_call([
                'qemu-img', 'convert',
                '-O', 'qcow2',
                str(self.disk_img_dist),
                str(self.disk_img_orig),
            ])

    def prepare_disk_image(self):
        if self.disk_img.is_file():
            self.disk_img.unlink()

        check_call([
            'qemu-img', 'create',
            '-f', 'qcow2',
            '-b', str(self.disk_img_orig),
            str(self.disk_img),
        ])
        check_call([
            'qemu-img', 'resize',
            str(self.disk_img),
            '10G',
        ])

    def create_cloud_init_image(self):
        cloud_init_yml = self.images / 'cloud-init.yml'
        self.cloud_init_img = self.images / 'cloud-init.img'
        with cloud_init_yml.open('w', encoding='utf8') as f:
            f.write(CLOUD_INIT_YML)

        check_call([
            'cloud-localds',
            str(self.cloud_init_img),
            str(cloud_init_yml),
        ])

    def build(self):
        self.check_arch(get_arch())
        self.download()
        self.prepare_disk_image()
        self.create_cloud_init_image()
        self.create_options_json()
        self.run_qemu()

    def create_options_json(self):
        options = self.get_options()
        with (self.images / 'options.json').open('w', encoding='utf8') as f:
            print(json.dumps(options, indent=2), file=f)


class Builder_x86_64(BaseBuilder):

    base_image_url = (
        'https://cloud-images.ubuntu.com/server/releases/16.04/release/'
        'ubuntu-16.04-server-cloudimg-amd64-disk1.img'
    )

    def run_qemu(self):
        check_call([
            'qemu-system-x86_64',
            '-enable-kvm',
            '-nographic',
            '-m', '512',
            '-netdev', 'user,id=user',
            '-device', 'virtio-net-pci,netdev=user',
            '-drive', 'index=0,media=disk,file=' + str(self.disk_img),
            '-drive', 'index=1,media=disk,format=raw,file=' + str(self.cloud_init_img),
        ])

    def get_options(self):
        return {}

    def check_arch(self, arch):
        assert arch == 'x86_64'


class Builder_arm64(BaseBuilder):

    base_image_url = (
        'https://cloud-images.ubuntu.com/server/releases/16.04/release/'
        'ubuntu-16.04-server-cloudimg-arm64-uefi1.img'
    )

    bios_url = (
        'https://releases.linaro.org/components/kernel/uefi-linaro/15.12/'
        'release/qemu64/QEMU_EFI.fd'
    )

    def __init__(self, images):
        super().__init__(images)
        self.arm_bios_fd = images / 'arm-bios.fd'

    def download(self):
        super().download()

        if not self.arm_bios_fd.is_file():
            check_call(['wget', str(self.bios_url), '-O', str(self.arm_bios_fd), '-q'])

    def qemu_args(self):
        return [
            'qemu-system-aarch64',
            '-nographic',
            '-m', '512',
            '-machine', 'virt',
            '-bios', str(self.arm_bios_fd),
            '-netdev', 'user,id=user',
            '-device', 'virtio-net-pci,netdev=user,romfile=',
            '-device', 'virtio-blk-device,drive=image',
            '-drive', 'if=none,id=image,file=' + str(self.disk_img),
            '-device', 'virtio-blk-device,drive=cloud-init',
            '-drive', 'if=none,id=cloud-init,format=raw,file=' + str(self.cloud_init_img),
        ]

    def run_qemu(self):
        check_call(self.qemu_args() + ['-cpu', 'host', '-enable-kvm'])

    def get_options(self):
        return {
            'native-arm': True,
        }

    def check_arch(self, arch):
        assert arch == 'aarch64'


class Builder_emuarm64(Builder_arm64):

    def __init__(self, images):
        super().__init__(images)
        self.arm_bios_fd = images / 'arm-bios.fd'

    def download(self):
        super().download()

        if not self.arm_bios_fd.is_file():
            check_call(['wget', str(self.bios_url), '-O', str(self.arm_bios_fd), '-q'])

    def run_qemu(self):
        check_call(self.qemu_args() + ['-cpu', 'cortex-a53'])

    def get_options(self):
        return {
            'emulate-arm': True,
        }

    def check_arch(self, arch):
        assert arch == 'x86_84'


PLATFORMS = {
    'cloud-x86_64': Builder_x86_64,
    'cloud-arm64': Builder_arm64,
    'cloud-emulated-arm64': Builder_emuarm64,
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

    parser = ArgumentParser()
    parser.add_argument('--platform',
                        default=default_platform,
                        choices=PLATFORMS.keys())
    options = parser.parse_args()

    images = Path(__file__).resolve().parent / 'images' / options.platform
    print("Preparing buildbot image for", options.platform)
    builder_cls = PLATFORMS[options.platform]

    images.mkdir()
    try:
        builder_cls(images).build()
    except:
        shutil.rmtree(str(images))
        raise


if __name__ == '__main__':
    main()
