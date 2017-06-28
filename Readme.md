## Liquid Buildbot
An automated build environment that uses [Kitchen](http://kitchen.ci) and QEMU
to create virtual machines based on [Ubuntu Cloud
Images](https://cloud-images.ubuntu.com). It supports the `x86_64` and
`aarch64` architectures.

### Usage
* Install kitchen:
    ```sh
    $ sudo apt install -y ruby cloud-utils
    $ sudo gem install test-kitchen kitchen-qemu
    ```

* Prepare the base image:
    ```sh
    $ ./prepare_cloud_image.py
    ```

* Run a build script:
    ```sh
    $ bin/build shared/scripts/build_odroid_image.sh
    ```

* Or spin up an instance by hand:

    ```sh
    $ VM=vm-$(uname -m)
    $ kitchen create $VM
    $ kitchen login $VM
    $ kitchen exec $VM -c "echo world > /mnt/shared/hello"
    $ cat shared/hello
    world
    $ kitchen destroy $VM
    ```

### Reference
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
