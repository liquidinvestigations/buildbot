#!/bin/bash
set -e

SETUPDIR=/tmp/liquid-setup
TARGET=/mnt/target
TEMPDIR=/tmp
OUTPUT=/mnt/shared/output

sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update
sudo apt install -y ansible git pv

git clone https://github.com/liquidinvestigations/setup $SETUPDIR

curl https://liquidinvestigations.org/images/ubuntu64-16.04-minimal-odroid-c2-20160815-4G.img.xz | xzcat > $TEMPDIR/odroid-c2.img

sudo losetup /dev/loop0 $TEMPDIR/odroid-c2.img -o 135266304
sudo mkdir -p $TARGET
sudo mount /dev/loop0 $TARGET
sudo mount --bind /proc $TARGET/proc
echo "nameserver 8.8.8.8" | sudo tee $TARGET/etc/resolv.conf

sudo apt-get install -qq qemu-user-static binfmt-support
sudo cp $(which qemu-arm-static) $TARGET/usr/bin

sudo chroot $TARGET apt-get update
sudo chroot $TARGET apt-get install -y python
sudo chroot $TARGET apt-get clean

cd $SETUPDIR/ansible
touch vars/config.yml
sudo ansible-playbook board_chroot.yml

sudo rm $TARGET/usr/bin/qemu-arm-static
sudo umount $TARGET
sudo losetup -d /dev/loop0

mkdir -p $OUTPUT
pv < $TEMPDIR/odroid-c2.img | xz > $OUTPUT/odroid-c2-liquid.img.xz
