## Liquid Buildbot
An automated build environment that uses [Kitchen](http://kitchen.ci) and QEMU
to create virtual machines based on [Ubuntu Cloud
Images](https://cloud-images.ubuntu.com). It supports the `x86_64` and
`aarch64` architectures.

### Setup
Install Kitchen with the QEMU driver:
```shell
$ sudo apt install -y ruby cloud-utils qemu-kvm genisoimage
$ sudo gem install test-kitchen kitchen-qemu
```

Prepare a QEMU image to run our instance:
```shell
$ ./prepare_cloud_image.py
```

### Usage
Run a script from the `shared` folder - it runs as `root` user in the instance:
```shell
$ ./buildbot run shared/scripts/build_odroid_image.sh
```

Log into an ephemeral machine:
```shell
$ ./buildbot login
```

Or control the instance using Kitchen commands:
```shell
$ instance="vm-$(uname -m)"
$ kitchen create $instance
$ kitchen login $instance
$ kitchen exec $instance -c "echo world > /mnt/shared/hello"
$ cat shared/hello
world
$ kitchen destroy $instance
```

### Converting the image
The build scripts produce "raw" images. You can convert them to VMware or
VirtualBox format. Append `-p` to get progress report.

```sh
qemu-img convert liquid-20170627-x86_64.img -O vmdk liquid-20170627-x86_64.vmdk
qemu-img convert liquid-20170627-x86_64.img -O vmi liquid-20170627-x86_64.vmi
```

### Reference
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
