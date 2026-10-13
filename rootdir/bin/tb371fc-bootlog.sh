#!/vendor/bin/sh
# Bring-up only: keep a trace of early boot in /metadata so a bootloop that
# dies before adbd can be diagnosed from recovery on a kernel without pstore.
# /metadata is small and also holds the /data encryption keys, so every log
# is capped (~6 MB per boot) and only the previous attempt is kept.
d=/metadata/bootlog
mkdir -p $d
rm -rf $d/2 $d/1
[ -d $d/0 ] && mv $d/0 $d/1
mkdir -p $d/0

# Stream the kernel log (from boot start) and logcat as they happen.
head -c 2097152 /dev/kmsg > $d/0/kmsg.txt 2>&1 &
(
    until /system/bin/logcat -b all -v threadtime -f $d/0/logcat.txt \
            -r 1024 -n 3 2>/dev/null; do
        sleep 1
    done
) &

i=0
while [ $i -lt 600 ]; do
    getprop > $d/0/props.txt 2>/dev/null
    sync
    sleep 1
    i=$((i + 1))
done
