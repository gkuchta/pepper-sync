This repoisotory should provide a debian package which creates a non-interactive system user and group called 'pepper-sync' and a directory '/data/video'. it will be targeting a raspberry pi5.

The user pepper-sync will be used to invoke `rclone copy tinycrypt: ./video/ --size-only --config /etc/pepper-sync/rclone.conf`, to copy new files for the pepper's ghost illusion down to the raspberry pi. If any of those flags appear incorrect, please let me know and we can corret them.

the /data/video directory should be owned by pepper-sync:pepper-sync, with permissions 755. our pepper-vidmix daemon and the ghostctrl controller will need to read video files contained here and list the directory contents.

rclone should be invoked via a systemd timer. the timer should trigger every hour.

the package can mark as dependencies anything necessary to satisfy this objective. e.g: rclone

stick to debian conventions where possible, but you're free to make implementation decisions. 
