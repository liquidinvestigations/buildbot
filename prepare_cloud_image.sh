#!/bin/bash
set -e

## Download Ubuntu cloud image and prepre it for use with Kitchen
# reference:
# * http://kitchen.ci
# * https://github.com/esmil/kitchen-qemu
# * https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
# * http://ubuntu-smoser.blogspot.ro/2013/02/using-ubuntu-cloud-images-without-cloud.html


img_url="http://cloud-images.ubuntu.com/server/releases/16.04/release/ubuntu-16.04-server-cloudimg-amd64-disk1.img"

set -x
mkdir -p ~/.config/kitchen-qemu/liquid-buildbot
cd ~/.config/kitchen-qemu/liquid-buildbot

if [ ! -f disk.img.orig ]; then
  wget $img_url -O disk.img.dist
  qemu-img convert -O qcow2 disk.img.dist disk.img.orig
fi

rm -f disk.img
qemu-img create -f qcow2 -b disk.img.orig disk.img

cat > cloud-init.yml <<EOF
#cloud-config
password: ubuntu
chpasswd: { expire: False }
ssh_pwauth: True
runcmd:
  - "touch /etc/cloud/cloud-init.disabled"
  - "poweroff"
EOF

cloud-localds cloud-init.img cloud-init.yml

qemu-system-x86_64 -enable-kvm -m 512 -nographic -netdev user,id=user -device virtio-net-pci,netdev=user -hda disk.img -hdb cloud-init.img
