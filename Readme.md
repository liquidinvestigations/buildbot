## Liquid Factory

An automated build environment that uses [Kitchen](http://kitchen.ci) and QEMU
to create virtual machines based on [Ubuntu Cloud
Images](https://cloud-images.ubuntu.com). It supports the `x86_64` and
`aarch64` architectures. The `aarch64` architecture can also be emulated
on `x86_64` build machines.

The build environment can also run VMs that it produces, to facilitate testing.

### Setup

Install required dependencies (assumes Ubuntu 16.04):
```shell
$ sudo apt install -y wget ruby ruby-dev build-essential cloud-utils qemu-kvm genisoimage python3-yaml
$ sudo gem install test-kitchen kitchen-qemu
$ sudo gem install rbnacl -v 4.0.2
$ sudo gem install rbnacl-libsodium bcrypt_pbkdf
```

Clone factory and prepare a QEMU image for your chosen platform:
```shell
$ git clone https://github.com/liquidinvestigations/factory.git
$ ./prepare_cloud_image.py --platform cloud-x86_64
$ ./prepare_cloud_image.py --platform emulated-cloud-arm64
```

Available platforms for `prepare_cloud_image.py`:
- `cloud-x86_64` (available only on `x86_64` hosts)
- `cloud-arm64` (available only on `aarch64` hosts)
- `emulated-cloud-arm64` (available only on `x86_64` hosts)


### Usage

Download the `setup` repo manually, or by using the `setup_setup` script (that
injects the configuration from `build_config.yml`, checking out the right
branch for setup):
```shell
$ ./setup_setup
```

Run a script from the `shared` folder - it runs as `root` user in the instance:
```shell
$ ./factory --platform emulated-cloud-arm64 run shared/scripts/build_odroid_image.sh
```

Log into an ephemeral machine:
```shell
$ ./factory login
```


## Automated testing

[Jenkins](https://jenkins.io/) is used for running automated tests on multiple
nodes of different architectures. Two types of nodes are being used: `x86_64`
and `arm64`.

The `Jenkinsfile` defines the stages run on each architecture.


### Reference
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
* http://odroid.com/dokuwiki/doku.php?id=en:c2_ubuntu_cloud
