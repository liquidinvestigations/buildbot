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

### Reference
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
* http://odroid.com/dokuwiki/doku.php?id=en:c2_ubuntu_cloud
