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
from subprocess import run

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
        self.run_qemu()


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


def main():
    images = Path(__file__).resolve().parent / 'images'
    Builder_x86_64(images).build()


if __name__ == '__main__':
    main()
