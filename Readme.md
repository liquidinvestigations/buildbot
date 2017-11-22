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

Both modes support the following options:

* `--image`: name of directory under `images` that is used to boot the image
  named `disk.img`, reading login settings from `config.json`. Defaults to
  `cloud-$ARCHITECTURE`, the image created by the `prepare-cloud-image` command

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

* `--vnc`: open a VNC server. The port number must be between 5900 and 5999.

    ```
    ./factory login --vnc 5900
    ```

* `--commit`: after the VM quits, save the changes to its disk.

    ```
    ./factory run --commit apt install build-essential -y
    ```

### Windows
Factory is mainly designed to run automated jobs in headless cloud VMs, but
with a bit of creative invocation, it can run windows! First let's create a
blank image.

```shell
./factory create win8 --size 64G
echo '{"qemu-args": ["-usbdevice", "tablet"]}' > images/win8/config.json
```

The second line is a fix to correlate mouse movement over VNC.

Then, get a hold of an ISO for Windows, we'll call it `windows8.iso` because I
tested on Windows 8. Also download [virtio-win.iso][] because it contains
essential drivers.

[virtio-win.iso]: https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

Let's boot the VM and install windows!

```shell
./factory console --image win8 --cdrom windows8.iso --cdrom virtio-win.iso --vnc 5901 --commit
```

Use a VNC client (e.g. [RealVNC][]) to connect to localhost port 5901. It
should open the VM's display which should show the Windows installer.

[RealVNC]: https://www.realvnc.com/download/viewer/

The installer won't detect the disk until you manually load drivers from the
`virtio-win` cdrom. Then proceed with the installation normally and boot into
your new account. If you want internet access, you must install the network
drivers from the same `virtio-win` cdrom.

When you're happy with your installation, shut down the windows. The `./factory
console` you invoked before should ask you:

```
Waiting for the VM to shut down ...
Commit? [Y/n]:
```

Press enter and your VM's hard drive will be saved.

Now is a good time to back up this image:

```shell
./factory export win8 | gzip -1 > win8-fresh-install.tgz
```

We can always import it later:
```shell
zcat win8-fresh-install.tgz | ./factory import win8-restored
```

Now let's run windows, even give it more resources:

```shell
./factory console --image win8 --smp 2 --memory 4096 --commit
```

When the VM shuts down, you can choose to save the VM's changes on disk, or
discard them. Omit the `--commit` flag to skip the prompt and always discard.

When you're done with an image, e.g. because you want to restore it from
backup, simply remove its folder from `images`:

```shell
rm -r images/win8
```
