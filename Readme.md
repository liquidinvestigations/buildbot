## Liquid Buildbot
An automated build environment that uses [Kitchen](http://kitchen.ci) and QEMU
to create virtual machines based on [Ubuntu Cloud
Images](https://cloud-images.ubuntu.com). It supports the `x86_64` and
`aarch64` architectures.

### Setup
Install required dependencies (assumes Ubuntu 16.04):
```shell
$ sudo apt install -y ruby cloud-utils qemu-kvm genisoimage
$ sudo gem install test-kitchen kitchen-qemu
$ sudo gem install rbnacl -v 4.0.2
$ sudo gem install rbnacl-libsodium bcrypt_pbkdf
$ sudo apt-get install python3-yaml
```

Clone buildbot and prepare a QEMU image:
```shell
$ git clone https://github.com/liquidinvestigations/buildbot.git
$ ./prepare_cloud_image.py
```

### Usage

Download the `setup` repo manually, or by using the `setup_setup` script:
```shell
$ ./setup_setup # uses configuration from build_config.yml
```

Run a script from the `shared` folder - it runs as `root` user in the instance:
```shell
$ ./buildbot run shared/scripts/build_odroid_image.sh
```

Log into an ephemeral machine:
```shell
$ ./buildbot login
```

For debugging, you can connect to the VM's serial console:
```shell
$ ./buildbot console
```

### Reference
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
* http://odroid.com/dokuwiki/doku.php?id=en:c2_ubuntu_cloud
