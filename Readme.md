## Liquid Buildbot
An automated build environment that uses [Kitchen](http://kitchen.ci) and QEMU
to create virtual machines based on [Ubuntu Cloud
Images](https://cloud-images.ubuntu.com).

### Usage
* Install kitchen:
    ```sh
    $ sudo apt install -y ruby
    $ sudo gem install test-kitchen
    $ sudo gem install kitchen-qemu
    ```

* Prepare the base image:
    ```sh
    $ ./prepare_cloud_image.py
    ```

* Spin up an instance and log in:
    ```sh
    $ kitchen create vm-x86-64
    $ kitchen login vm-x86-64
    ```

* Run a command, save the output to the shared folder:
    ```sh
    $ kitchen exec vm-x86-64 -c "echo world > /mnt/shared/hello"
    $ cat shared/hello
    world
    ```

* Tear down the instance:
    ```sh
    $ kitchen destroy vm-x86-64
    ```

### ARM64 support
To run the VM on ARM64, replace `vm-x86-64` with `vm-aarch64` when calling
`kitchen`. The `prepare_cloud_image.py` script auto-detects the current
architecture and prepares the VM image accordingly.

### Reference
* https://github.com/esmil/kitchen-qemu
* https://help.ubuntu.com/community/UEC/Images#Ubuntu_Cloud_Guest_images_on_12.04_LTS_.28Precise.29_and_beyond_using_NoCloud
