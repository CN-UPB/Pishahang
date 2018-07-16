#!/bin/sh
OPENMANO=/home/openmanod/bin/openmano
OPENMANO_TENANT=`$OPENMANO tenant-create mytenant --description=mytenant`
if [ $? -ne 0 ]; then
    OPENMANO_TENANT=`$OPENMANO tenant-list mytenant`
fi
echo $OPENMANO_TENANT |gawk '{print $1}'
