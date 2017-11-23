## Liquid Factory

A command-line virtual machine runner that uses QEMU to create virtual machines
based on [Ubuntu Cloud Images](https://cloud-images.ubuntu.com). It supports
the `x86_64` and `aarch64` architectures.

### Setup
Install factory and its dependencies (assumes Ubuntu 16.04):

```shell
$ sudo apt install -y wget qemu-kvm qemu-utils xz-utils
$ python3 <(curl -sL https://github.com/liquidinvestigations/factory/raw/master/install.py) factory
$ cd factory
$ ./factory echo hello world
```


### Building base imagse
The installer described above downloads a pre-built cloud image, but you can
build one yourself:

$ ./factory prepare-cloud-image


### Usage
Factory works in two modes: `login` starts a VM and logs in via SSH; `run`
executes a command as root. In both cases, the VM runs with a temporary disk,
and it's destroyed as soon as the command/login finishes.

* `login`:

    ```
    ./factory login
    ```

* `run`:

    ```
    ./factory run whoami
    ```

Common options, before the `login` or `run` command:

* `--platform`: name of directory under `images` that is used to boot the image
  named `disk.img`, reading login settings from `config.json`. Defaults to
  `cloud-$ARCHITECTURE`, the image created by the `prepare-cloud-image` command

Both modes support the following options:

* `--share`: share a folder with the VM. Can be used multiple times. The first
  path is the local path, the second is the mount point inside the VM.

    ```
    ./factory login --share local/path/shared:/mnt/shared
    ```

* `--smp`: number of cores, default is `1`

    ```
    ./factory login --smp 2
    ```

* `--memory`: RAM in megabytes, default is `512`

    ```
    ./factory login --memory 2048
    ```

* `--tcp`: forward a TCP port. The first number is the host port, the second
  number is the VM port.

    ```
    ./factory login --tcp 8080:80
    ```

* `--udp`: forward a UDP port. The first number is the host port, the second
  number is the VM port.

    ```
    ./factory login --udp 1053:53
    ```
