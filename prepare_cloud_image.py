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

def main(images):
    img_url = 'http://cloud-images.ubuntu.com/server/releases/16.04/release/ubuntu-16.04-server-cloudimg-amd64-disk1.img'

    disk_img_orig = images / 'disk.img.orig'
    disk_img_dist = images / 'disk.img.dist'
    disk_img = images / 'disk.img'

    if not disk_img_orig.is_file():
        run(['wget', img_url, '-O', str(disk_img_dist)])
        run(['qemu-img', 'convert', '-O', 'qcow2',
            str(disk_img_dist), str(disk_img_orig)])

    if disk_img.is_file():
        disk_img.unlink()

    run(['qemu-img', 'create', '-f', 'qcow2',
        '-b', str(disk_img_orig), str(disk_img)])
    run(['qemu-img', 'resize', str(disk_img), '10G'])

    cloud_init_yml = images / 'cloud-init.yml'
    cloud_init_img = images / 'cloud-init.img'
    with cloud_init_yml.open('w', encoding='utf8') as f:
        f.write(CLOUD_INIT_YML)

    run(['cloud-localds', str(cloud_init_img), str(cloud_init_yml)])

    run([
        'qemu-system-x86_64',
        '-enable-kvm', '-m', '512', '-nographic',
        '-netdev', 'user,id=user', '-device', 'virtio-net-pci,netdev=user',
        '-hda', str(disk_img),
        '-hdb', str(cloud_init_img),
    ])

if __name__ == '__main__':
    images = Path(__file__).resolve().parent / 'images'
    main(images)
