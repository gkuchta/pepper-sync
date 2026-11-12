# pepper-sync

A Debian package for Raspberry Pi 5 running Raspberry Pi OS or Debian with
systemd. The package contains no architecture-specific code (`Architecture: all`),
so the same `.deb` works on arm64 and other Debian architectures.

Installation creates a system user and group named `pepper-sync`, with no login
shell or home directory, and `/data/video`, owned by `pepper-sync:pepper-sync`
with mode `0755`. New downloads use umask `0022`, allowing `pepper-vidmix` and
`ghostctrl` to read files and list directories without joining the service group.
Existing files' permissions are not changed. `/data` must also allow these
readers to traverse it if you have provisioned it yourself.

## Build and install

On Debian or Raspberry Pi OS Bookworm or newer:

```sh
sudo apt install build-essential debhelper
dpkg-buildpackage --build=binary --no-sign
sudo apt install ../pepper-sync_0.1.0_all.deb
```

Runtime dependencies include `adduser`, `rclone`, and `systemd`. Debhelper handles
enabling and starting the timer on installation and preserving an administrator's
disabled timer across upgrades. Removal stops the timer and any active copy.
Upgrades leave an active copy running rather than interrupting it.

## Configure the remote

Create a working rclone configuration containing the `tinycrypt` remote and any
underlying remotes it uses. For example, run `rclone config` on a trusted machine
and transfer its configuration securely to the Pi. Install that file with:

```sh
sudo install -o pepper-sync -g pepper-sync -m 0600 ./rclone.conf /etc/pepper-sync/rclone.conf
sudo systemctl start pepper-sync.service
```

The configuration directory is owned by `pepper-sync` with mode `0700` so rclone
can save refreshed OAuth tokens without exposing credentials to video readers.
Use a configuration that works unattended; an encrypted config requires a
separately provisioned non-interactive password source such as rclone's
`RCLONE_PASSWORD_COMMAND` through a systemd override. The service disables password
prompts. Remotes must not rely on files under `/home` or `/root`, which the service
sandbox hides.

No credentials or placeholder `rclone.conf` are shipped. Until that file exists,
systemd skips copy attempts. After provisioning it, the next hourly run works
automatically; the manual start above performs the initial download immediately.

## Operation

The service runs as `pepper-sync` and invokes:

```sh
/usr/bin/rclone copy tinycrypt: /data/tinygarretts/ --size-only --config /etc/pepper-sync/rclone.conf --ask-password=false --log-level INFO
```

`/data/tinygarretts/` is the absolute form of the requested `./video/` when run from
`/data`. `--size-only` skips an existing destination file of the same size even
when its contents changed. Differently sized files can be replaced. `copy`
preserves local files when they disappear from the remote; it does not mirror
deletions. See the [rclone copy documentation](https://rclone.org/commands/rclone_copy/)
and [size-only documentation](https://rclone.org/docs/#size-only).

The timer runs at each clock hour (within systemd's default one-minute accuracy).
`Persistent=true` runs one catch-up copy after downtime. A copy may take longer
than an hour; systemd does not start a second instance while it is still running.
The service waits for the mount containing `/data/tinygarretts` and requests network
readiness. A failed download is logged and is tried again at the next timer tick.

```sh
systemctl list-timers pepper-sync.timer
systemctl status pepper-sync.service pepper-sync.timer
journalctl -u pepper-sync.service
sudo systemctl disable --now pepper-sync.timer  # stop future scheduled copies
sudo systemctl stop pepper-sync.service        # stop an active copy
```

Service writes are limited to the video directory, private temporary storage,
the rclone cache, and its configuration directory. Downloaded videos, credentials,
and the service account are retained on removal and purge so files are not lost
and their numeric owner cannot be reassigned accidentally. Remove these manually
only when no longer needed. `/data/video` is an intentional site-specific path
required by this project rather than a standard Debian state directory.

## Checks

```sh
systemd-analyze verify debian/pepper-sync.service debian/pepper-sync.timer
python3 tests/smoke.py
```

The smoke check uses a temporary local `tinycrypt` alias and the service's actual
rclone command to check recursive downloads, readable permissions, size-only
skipping, replacement of differently sized files, and preservation of local files.
It needs `python3` and `rclone`; it does not use remote credentials or install the
package. Test installation and timer execution on a disposable systemd machine
before deploying to the Pi.

Package maintainer metadata uses a local placeholder address. Set the real
maintainer address and choose a redistribution license before publishing.
