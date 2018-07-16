#! /bin/bash

# 
#   Copyright 2016 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# Author(s): Anil Gunturu
# Creation Date: 07/24/2014
# 

##
# This script is used to copy the riftware software into the qcow image
# This script must be run on the grunt machine as root
##

set -x
set -e

if ! [ $# -eq 1 ]; then
    echo "Usage: $0 <ping-pong-ns-dir>"
    echo "       Example:"
    echo "       $0 /net/boson/home1/agunturu/lepton/atg/modules/core/mc/examples/ping_pong_ns"
    exit 1
fi

# Currently returning 0 on error as this script fails in Bangalore
# systems and causes the jenkins spot_debug to fail
function cleanup {
  if [ "$(ls -A $MOUNT_PT)" ]; then
    guestunmount $MOUNT_PT
  fi
  exit 0
}
trap cleanup EXIT

MOUNT_PT=ping_pong/mnt$$

if  [ -d $MOUNT_PT ]; then
  echo "ping_pong_mnt directory exists - deleting..!!"
  guestunmount $MOUNT_PT || true
  rm -rf ping_pong
fi

mkdir -p $MOUNT_PT
FC20QCOW=Fedora-x86_64-20-20131211.1-sda.qcow2
PINGQCOW=Fedora-x86_64-20-20131211.1-sda-ping.qcow2
PONGQCOW=Fedora-x86_64-20-20131211.1-sda-pong.qcow2

if [ ! -e ${RIFT_ROOT}/images/${FC20QCOW} ]; then
    echo >&2 "Warn: Cannot prepare ping_pong qcow due to missing FC20 image: ${RIFT_ROOT}/images/${FC20QCOW}"
    exit 0
fi

echo "Copying $FC20QCOW"
cp ${RIFT_ROOT}/images/${FC20QCOW} ping_pong/${PINGQCOW}
chmod +w ping_pong/${PINGQCOW}
cp ${RIFT_ROOT}/images/${FC20QCOW} ping_pong/${PONGQCOW}
chmod +w ping_pong/${PONGQCOW}

CURRENT_DIR=$PWD
echo "Mounting guestfs for $PINGQCOW"
guestmount -a ping_pong/$PINGQCOW -m /dev/sda1 $MOUNT_PT

echo "Setting up resolv.conf"
# removed RIFT.io lab-centric setup in RIFT-11991
#echo "search lab.riftio.com eng.riftio.com riftio.com" >  $MOUNT_PT/etc/resolv.conf
#echo "nameserver 10.64.1.3" >>  $MOUNT_PT/etc/resolv.conf
#echo "PEERDNS=no" >> $MOUNT_PT/etc/sysconfig/network-scripts/ifcfg-eth0

# add a valid DNS server just in case
echo "nameserver 8.8.8.8" >  $MOUNT_PT/etc/resolv.conf
echo "DEFROUTE=yes" >> $MOUNT_PT/etc/sysconfig/network-scripts/ifcfg-eth0

for i in 1 2
do
    cat <<EOF >> $MOUNT_PT/etc/sysconfig/network-scripts/ifcfg-eth$i
DEVICE="eth$i"
BOOTPROTO="dhcp"
ONBOOT="no"
TYPE="Ethernet"
DEFROUTE=no
PEERDNS=no
EOF
done


echo "Copying ping/pong ns..."
cd $MOUNT_PT/opt
mkdir rift
cd rift
cp -r $1 .
cd $CURRENT_DIR
mv $MOUNT_PT/opt/rift/ping_pong_ns/ping.service $MOUNT_PT/etc/systemd/system
cp -ar /usr/lib/python2.7/site-packages/tornado $MOUNT_PT/usr/lib/python2.7/site-packages/
guestunmount $MOUNT_PT

echo "Mounting guestfs for $PINGQCOW"
guestmount -a ping_pong/$PONGQCOW -m /dev/sda1 $MOUNT_PT

echo "Setting up resolv.conf"
echo "search lab.riftio.com eng.riftio.com riftio.com" >  $MOUNT_PT/etc/resolv.conf
echo "nameserver 10.64.1.3" >>  $MOUNT_PT/etc/resolv.conf
echo "PEERDNS=no" >> $MOUNT_PT/etc/sysconfig/network-scripts/ifcfg-eth0
echo "DEFROUTE=yes" >> $MOUNT_PT/etc/sysconfig/network-scripts/ifcfg-eth0

for i in 1 2
do
    cat <<EOF >> $MOUNT_PT/etc/sysconfig/network-scripts/ifcfg-eth$i
DEVICE="eth$i"
BOOTPROTO="dhcp"
ONBOOT="no"
DEFROUTE=no
TYPE="Ethernet"
PEERDNS=no
EOF
done

echo "Copying ping/pong ns..."
cd $MOUNT_PT/opt
mkdir rift
cd rift
cp -r $1 .
cd $CURRENT_DIR
cp -ar /usr/lib/python2.7/site-packages/tornado $MOUNT_PT/usr/lib/python2.7/site-packages/
mv $MOUNT_PT/opt/rift/ping_pong_ns/pong.service $MOUNT_PT/etc/systemd/system
guestunmount $MOUNT_PT
