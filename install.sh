#! /bin/sh

DIR0=`dirname $0`
DIR=`realpath $DIR0`
grep lighttree.pl /etc/rc.local > /dev/null || \
    sed -i.pre-derbynet \
        -e '/^exit 0/ i \
DIR/lighttree.pl\
'\
        /etc/rc.local

sed -i -e "s!DIR!$DIR!" /etc/rc.local
