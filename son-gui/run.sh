#!/bin/bash

LOCKFILE=/run/apache2/apache2.pid

# Previous apache should execute successfully:

[ -f $LOCKFILE ] && exit 0

# Upon exit, remove lockfile.

trap "{ rm -f $LOCKFILE ; exit 255; }" EXIT

# Start apache
/usr/sbin/apache2ctl -D FOREGROUND
