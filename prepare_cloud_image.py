#!/usr/bin/env python3

"""
Download Ubuntu cloud image and prepre it for use with Kitchen

reference:
* http://kitchen.ci
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
* http://ubuntu-smoser.blogspot.ro/2013/02/using-ubuntu-cloud-images-without-cloud.html
"""

from pathlib import Path
from subprocess import run, PIPE
from argparse import ArgumentParser

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

    kitchen_yml_template = """\
driver:
  name: qemu

platforms:
  - name: {name}
    driver:
      image_path: ./images
      image: disk.img
      username: ubuntu
      password: ubuntu
      hostshares:
        - path: shared
          mountpoint: /mnt/shared
{extra}
suites:
  - name: vm
"""

    def __init__(self, images):
        self.images = images
        self.disk_img_orig = images / 'disk.img.orig'
        self.disk_img_dist = images / 'disk.img.dist'
        self.disk_img = images / 'disk.img'

    def download(self):
        if not self.disk_img_orig.is_file():
            run([
                'wget', str(self.base_image_url),
                '-O', str(self.disk_img_dist),
            ])
            run([
                'qemu-img', 'convert',
                '-O', 'qcow2',
                str(self.disk_img_dist),
                str(self.disk_img_orig),
            ])

    def prepare_disk_image(self):
        if self.disk_img.is_file():
            self.disk_img.unlink()

        run([
            'qemu-img', 'create',
            '-f', 'qcow2',
            '-b', str(self.disk_img_orig),
            str(self.disk_img),
        ])
        run([
            'qemu-img', 'resize',
            str(self.disk_img),
            '10G',
        ])

    def create_cloud_init_image(self):
        cloud_init_yml = self.images / 'cloud-init.yml'
        self.cloud_init_img = self.images / 'cloud-init.img'
        with cloud_init_yml.open('w', encoding='utf8') as f:
            f.write(CLOUD_INIT_YML)

        run([
            'cloud-localds',
            str(self.cloud_init_img),
            str(cloud_init_yml),
        ])

    def build(self):
        self.download()
        self.prepare_disk_image()
        self.create_cloud_init_image()
        self.create_kitchen_yml()
        self.run_qemu()

    def create_kitchen_yml(self, name, extra = ()):
        extra_fmt = ''
        for l in extra:
            extra_fmt += '      ' + l + '\n'

        with open('.kitchen.yml', 'w') as f:
            f.write(self.kitchen_yml_template.format(name=name, extra=extra_fmt))


class Builder_x86_64(BaseBuilder):

    base_image_url = (
        'https://cloud-images.ubuntu.com/server/releases/16.04/release/'
        'ubuntu-16.04-server-cloudimg-amd64-disk1.img'
    )

    def run_qemu(self):
        run([
            'qemu-system-x86_64',
            '-enable-kvm',
            '-nographic',
            '-m', '512',
            '-netdev', 'user,id=user',
            '-device', 'virtio-net-pci,netdev=user',
            '-hda', str(self.disk_img),
            '-hdb', str(self.cloud_init_img),
        ])

    def create_kitchen_yml(self, name='x86_64', extra=()):
        super().create_kitchen_yml(name, extra)


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
            run(['wget', str(self.bios_url), '-O', str(self.arm_bios_fd)])

    def qemu_args(self):
        return [
            'qemu-system-aarch64',
            '-nographic',
            '-m', '512',
            '-machine', 'virt',
            '-bios', str(self.arm_bios_fd),
            '-netdev', 'user,id=user',
            '-device', 'virtio-net-pci,netdev=user',
            '-device', 'virtio-blk-device,drive=image',
            '-drive', 'if=none,id=image,file=' + str(self.disk_img),
            '-device', 'virtio-blk-device,drive=cloud-init',
            '-drive', 'if=none,id=cloud-init,file=' + str(self.cloud_init_img),
        ]

    def run_qemu(self):
        run(self.qemu_args() + [ '-cpu', 'host', '-enable-kvm' ])

    def create_kitchen_yml(self, name='aarch64', extra=()):
        super().create_kitchen_yml(name,
            ( 'bios: ' + str(self.arm_bios_fd),
              'binary: ./qemu-hacked-arm', ) + extra)


class Builder_emuarm64(Builder_arm64):

    def __init__(self, images):
        super().__init__(images)
        self.arm_bios_fd = images / 'arm-bios.fd'

    def download(self):
        super().download()

        if not self.arm_bios_fd.is_file():
            run(['wget', str(self.bios_url), '-O', str(self.arm_bios_fd)])

    def run_qemu(self):
        run(self.qemu_args() + [ '-cpu', 'cortex-a53' ])

    def create_kitchen_yml(self, name='aarch64', extra=()):
        super().create_kitchen_yml(name,
            ( 'args: [ cpu: cortex-a53 ]',
              'kvm: false' ) + extra)


def main():
    images = Path(__file__).resolve().parent / 'images'

    parser = ArgumentParser()
    parser.add_argument('--emulate-arm64', action='store_true')
    options = parser.parse_args()

    if options.emulate_arm64:
        builder_cls = Builder_emuarm64
    else:
        arch = run(['uname', '-m'], stdout=PIPE).stdout.decode('latin1').strip()
        if arch == 'x86_64':
            builder_cls = Builder_x86_64
        elif arch == 'aarch64':
            builder_cls = Builder_arm64
        else:
            raise RuntimeError("Can not detect architecture")

    builder_cls(images).build()


if __name__ == '__main__':
    main()
