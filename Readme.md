## Liquid Factory

An automated build environment that uses [Kitchen](http://kitchen.ci) and QEMU
to create virtual machines based on [Ubuntu Cloud
Images](https://cloud-images.ubuntu.com). It supports the `x86_64` and
`aarch64` architectures.

The build environment can also run VMs that it produces, to facilitate testing.

### Setup

Install required dependencies (assumes Ubuntu 16.04):
```shell
$ sudo apt install -y wget ruby ruby-dev build-essential cloud-utils qemu-kvm genisoimage
$ sudo gem install test-kitchen kitchen-qemu
$ sudo gem install rbnacl -v 4.0.2
$ sudo gem install rbnacl-libsodium bcrypt_pbkdf
```

Clone factory and prepare a QEMU image for your chosen platform. By default,
factory will download and cache original Ubuntu cloud images in `~/.factory`,
but you can set another path with the `--db` argument.
```shell
$ git clone https://github.com/liquidinvestigations/factory.git
$ ./factory prepare-cloud-image --platform cloud-x86_64
```

Available platforms for `prepare_cloud_image.py`:
- `cloud-x86_64` (available only on `x86_64` hosts)
- `cloud-arm64` (available only on `aarch64` hosts)


### Usage

Run a script from the `shared` folder - it runs as `root` user in the instance:
```shell
$ ./factory --platform cloud-arm64 run --share shared:/mnt/shared /mnt/shared/scripts/build_odroid_image.sh
```

Log into an ephemeral machine with the default image for your platform (purchased separately):
```shell
$ ./factory login
```

#### Command line options

- `--platform`: name of directory under `/images` that is used to boot the image named `disk.img`, reading login settings from `config.json`
- `--share HOST:GUEST`: shares a folder with the VM
- `--tcp HOST:GUEST`: tcp port forwarding
- `--memory N`: in megabytes
- `--smp N`: number of virtual processors


## Automated testing

[Jenkins](https://jenkins.io/) is used for running automated tests on multiple
nodes of different architectures. Two types of nodes are being used: `x86_64`
and `arm64`.

The `Jenkinsfile` defines the stages run on each architecture.


### Reference
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
* http://odroid.com/dokuwiki/doku.php?id=en:c2_ubuntu_cloud
