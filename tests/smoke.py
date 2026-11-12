#!/usr/bin/env python3
"""Exercise the packaged rclone command without credentials or root access."""

import configparser
import os
from pathlib import Path
import shlex
import stat
import subprocess
import tempfile


def main():
    service = configparser.ConfigParser(interpolation=None)
    service.read(Path(__file__).resolve().parents[1] / "debian/pepper-sync.service")
    command = shlex.split(service["Service"]["ExecStart"])
    mask = int(service["Service"]["UMask"], 8)

    with tempfile.TemporaryDirectory(prefix="pepper-sync-smoke-") as directory:
        root = Path(directory)
        source = root / "source"
        destination = root / "tinygarretts"
        source.mkdir()
        (source / "nested").mkdir()
        (source / "nested/clip.mp4").write_bytes(b"first video")
        config = root / "rclone.conf"
        config.write_text(f"[tinycrypt]\ntype = alias\nremote = {source}\n")
        os.chmod(config, 0o600)
        command[command.index("/data/tinygarretts/")] = str(destination)
        command[command.index("--config") + 1] = str(config)

        # Ignore any developer's rclone environment when exercising the fixture.
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith("RCLONE_")}
        environment["RCLONE_CACHE_DIR"] = str(root / "cache")

        def copy():
            previous_mask = os.umask(mask)
            try:
                subprocess.run(command, check=True, env=environment)
            finally:
                os.umask(previous_mask)

        copy()
        downloaded = destination / "nested/clip.mp4"
        assert downloaded.read_bytes() == b"first video"
        assert stat.S_IMODE(downloaded.stat().st_mode) == 0o644
        assert stat.S_IMODE(downloaded.parent.stat().st_mode) == 0o755

        # A content change of equal length must be skipped with --size-only.
        (source / "nested/clip.mp4").write_bytes(b"other video")
        copy()
        assert downloaded.read_bytes() == b"first video"

        (source / "nested/clip.mp4").write_bytes(b"a longer replacement video")
        copy()
        assert downloaded.read_bytes() == b"a longer replacement video"

        (source / "nested/clip.mp4").unlink()
        copy()
        assert downloaded.read_bytes() == b"a longer replacement video"

    print("PASS: downloads, permissions, size-only comparison, and local retention")


if __name__ == "__main__":
    main()
