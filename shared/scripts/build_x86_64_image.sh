#!/bin/bash

###
# Build a Liquid image and save it to `shared/output`
###

set -e

SETUPDIR=/tmp/liquid-setup
TARGET=/mnt/target
TEMPDIR=/tmp
OUTPUT=/mnt/shared/output

set -x

apt-add-repository -y ppa:ansible/ansible
apt-get update
apt-get install -y ansible git pv

git clone https://github.com/liquidinvestigations/setup $SETUPDIR

# The image needs to be downloaded manually from:
# https://cloud-images.ubuntu.com/server/releases/16.04/release/ubuntu-16.04-server-cloudimg-amd64-disk1.img
# and converted to raw format using:
# qemu-img convert -f qcow2 -O raw ubuntu-16.04-server-cloudimg-amd64-disk1.img ubuntu-raw.img

# It also needs to be resized to 4 gigabytes, using
# truncate -s 4G ubuntu-raw.img
# then deleting and recreating the partition inside, and running
# resize2fs to resize the filesystem.

# Finally, it needs to be placed in the shared directory, so the VM can see it.

#curl https://liquidinvestigations.org/images/ubuntu64-16.04-minimal-odroid-c2-20160815-4G.img.xz | xzcat > $TEMPDIR/odroid-c2.img
#cp /mnt/shared/ubuntu-raw.img $TEMPDIR

losetup /dev/loop0 /mnt/shared/ubuntu-raw.img -o 1048576
mkdir -p $TARGET
mount /dev/loop0 $TARGET
mount --bind /proc $TARGET/proc
mount --bind /dev $TARGET/dev
rm -f $TARGET/etc/resolv.conf
echo "nameserver 8.8.8.8" > $TARGET/etc/resolv.conf

chroot $TARGET apt-get update
chroot $TARGET apt-get install -y python
chroot $TARGET apt-get clean

cd $SETUPDIR/ansible
touch vars/config.yml
ansible-playbook board_chroot.yml

umount $TARGET/proc
umount $TARGET/dev
umount $TARGET
losetup -d /dev/loop0

#mkdir -p $OUTPUT
#pv < $TEMPDIR/odroid-c2.img | xz -0 > $OUTPUT/odroid-c2-liquid.img.xz
