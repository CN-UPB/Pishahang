#!/bin/sh
HOME=/home/openmanod
OPENMANO=$HOME/bin/openmano
export OPENMANO_TENANT=$4

OPENMANO_DATACENTER=`$OPENMANO datacenter-list myov`
if [ $? -eq 0 ]; then
    # If the datacenter exists, the current approach is to delete the existing
    # one and create a new one. We may want to change this behavior to retain
    # the existing datacenter, but this script will also go away in favour of
    # a python API to OpenMano

    # If the datacenter exists, remove all traces of it before continuing
    OPENMANO_DATACENTER=`echo $OPENMANO_DATACENTER |gawk '{print $1}'`

    # Delete netmap
    $OPENMANO datacenter-netmap-delete --all -f --datacenter $OPENMANO_DATACENTER

    # detach
    $OPENMANO datacenter-detach -a $OPENMANO_DATACENTER

    # Make sure the datacenter is deleted
    $OPENMANO datacenter-delete --force myov

    OPENMANO_DATACENTER=`$OPENMANO datacenter-create myov http://$1:$2/openvim`
fi
OPENMANO_DATACENTER=`echo $OPENMANO_DATACENTER |gawk '{print $1}'`


# if ! grep -q "^export OPENMANO_DATACENTER" $HOME/.bashrc
# then
#     echo "export OPENMANO_DATACENTER=$OPENMANO_DATACENTER " >> $HOME/.bashrc
# fi

$OPENMANO datacenter-attach myov --vim-tenant-id $3
$OPENMANO datacenter-netmap-import -f --datacenter $OPENMANO_DATACENTER
