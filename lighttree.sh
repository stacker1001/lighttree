#! /bin/sh

# Loop forever, just in case there's an error of some kind.
# Ctrl-C to exit
while true ; do
    `dirname $0`/xmastree.pl
done
