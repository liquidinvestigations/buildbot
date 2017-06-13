## Liquid Buildbot
An automated build environment that uses [Kitchen](http://kitchen.ci) and QEMU
to create virtual machines based on [Ubuntu Cloud
Imaages](https://cloud-images.ubuntu.com).

### Usage
* Install kitchen:
    ```sh
    gem install test-kitchen
    gem install kitchen-qemu
    ```

* Prepare the base image:
    ```sh
    ./prepare_cloud_image.sh
    ```

* Spin up an instance and log in:
    ```sh
    kitchen create default-ubuntu-1604
    kitchen login default-ubuntu-1604
    ```

* Run a command:
    ```sh
    kitchen exec default-ubuntu-1604 -c "df -h /"
    ```

* Tear down the instance:
    ```sh
    kitchen destroy default-ubuntu-1604
    ```
