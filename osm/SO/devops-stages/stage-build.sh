#!/bin/sh
rm -rf .build
IM_FILES="
ietf-l2-topology.yang
ietf-network-topology.yang
ietf-network.yang
mano-rift-groupings.yang
mano-types.yang
nsd-base.yang
nsd.yang
nsr.yang
odl-network-topology.yang
project-nsd.yang
project-vnfd.yang
vlr.yang
vnfd-base.yang
vnfd.yang
vnffgd.yang
vnfr.yang
"
echo "installing IM files"
# note that this cannot be inside the SO or else CMAKE will find it 
tmp=$(mktemp -d)
git clone $(dirname $(git remote get-url origin))/IM.git $tmp
for file in $IM_FILES; do 
    rm -f models/plugins/yang/$file
    cp $tmp/models/yang/$file models/plugins/yang
done
rm -rf $tmp
make NOT_DEVELOPER_BUILD=TRUE -j16 package

