#!/bin/bash

##
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
# This file is part of openmano
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact with: nfvlabs@tid.es
##

#This script can be used as a basic test of openmano.
#WARNING: It destroy the database content


function usage(){
    echo -e "usage: ${BASH_SOURCE[0]} [OPTIONS] <action>\n  test openmano with fake tenant, datancenters, etc."\
            "It assumes that you have configured openmano cli with HOST,PORT,TENANT with environment variables"
            "If not, it will use by default localhost:9080 and creates a new TENANT"
    echo -e "    -h --help        shows this help"
}

function is_valid_uuid(){
    echo "$1" | grep -q -E '^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$' && return 0
    return 1
}

DIRNAME=$(dirname $(readlink -f ${BASH_SOURCE[0]}))
DIRmano=$(dirname $DIRNAME)
DIRscript=${DIRmano}/scripts

#detect paths of executables, preceding the relative paths
openmano=openmano && [[ -x "${DIRmano}/openmano" ]] && openmano="${DIRmano}/openmano"
service_openmano=service-openmano && [[ -x "$DIRscript/service-openmano" ]] &&
    service_openmano="$DIRscript/service-openmano"
initopenvim="initopenvim"
openvim="openvim"

function _exit()
{
    EXIT_STATUS=$1
    for item in $ToDelete
    do
        command=${item%%:*}
        uuid=${item#*:}
        [[ $command == "datacenter-detach" ]] && force="" || force=-f
        printf "%-50s" "$command $uuid:"
        ! $openmano $command $uuid $force >> /dev/null && echo FAIL && EXIT_STATUS=1 || echo OK
     done
    [[ ${BASH_SOURCE[0]} != $0 ]] && return $1 || exit $EXIT_STATUS
}


# process options
source ${DIRscript}/get-options.sh "force:-f help:h insert-bashrc init-openvim:initopenvim install-openvim screen" \
                $* || _exit 1

# help
[ -n "$option_help" ] && usage && _exit 0


ToDelete=""
DCs="dc-fake1-openstack dc-fake2-openvim" #dc-fake3-vmware
Ts="fake-tenant1 fake-tenand2"
SDNs="sdn-fake1-opendaylight sdn-fake2-floodlight sdn-fake3-onos"

for T in $Ts
do
    printf "%-50s" "Creating fake tenant '$T':"
    ! result=`$openmano tenant-create "$T"` && echo FAIL && echo "    $result" && _exit 1
    tenant=`echo $result |gawk '{print $1}'`
    ! is_valid_uuid $tenant && echo "FAIL" && echo "    $result" && _exit 1
    echo $tenant
    ToDelete="tenant-delete:$tenant $ToDelete"
    [[ -z "$OPENMANO_TENANT" ]] && export OPENMANO_TENANT=$tenant
done

index=0
for DC in $DCs
do
    index=$((index+1))
    printf "%-50s" "Creating datacenter '$DC':"
    ! result=`$openmano datacenter-create "$DC" "http://$DC/v2.0" --type=${DC##*-} --config='{insecure: True}'` &&
        echo FAIL && echo "    $result" && _exit 1
    datacenter=`echo $result |gawk '{print $1}'`
    ! is_valid_uuid $datacenter && echo "FAIL" && echo "    $result" && _exit 1
    echo $datacenter
    eval DC${index}=$datacenter
    ToDelete="datacenter-delete:$datacenter $ToDelete"
    [[ -z "$datacenter_empty" ]] && datacenter_empty=datacenter

    printf "%-50s" "Attaching openmano tenant to the datacenter:"
    ! result=`$openmano datacenter-attach "$DC" --vim-tenant-name=osm --config='{insecure: False}'` &&
        echo FAIL && echo "    $result" && _exit 1
    ToDelete="datacenter-detach:$datacenter $ToDelete"
    echo OK
done

printf "%-50s" "Datacenter list:"
! result=`$openmano datacenter-list` &&
    echo  "FAIL" && echo "    $result" && _exit 1
for verbose in "" -v -vv -vvv
do
    ! result=`$openmano datacenter-list "$DC" $verbose` &&
        echo  "FAIL" && echo "    $result" && _exit 1
done
echo OK

dpid_prefix=55:56:57:58:59:60:61:0
dpid_sufix=0
for SDN in $SDNs
do
    printf "%-50s" "Creating SDN controller '$SDN':"
    ! result=`$openmano sdn-controller-create "$SDN" --ip 4.5.6.7 --port 80 --type=${SDN##*-} \
        --user user --passwd p --dpid=${dpid_prefix}${dpid_sufix}` && echo "FAIL" && echo "    $result" && _exit 1
    sdn=`echo $result |gawk '{print $1}'`
    #check a valid uuid is obtained
    ! is_valid_uuid $sdn && echo "FAIL" && echo "    $result" && _exit 1
    echo $sdn
    ToDelete="sdn-controller-delete:$sdn $ToDelete"
    dpid_sufix=$((dpid_sufix+1))

done
printf "%-50s" "Edit SDN-controller:"
for edit in user=u password=p ip=5.6.6.7 port=81 name=name dpid=45:55:54:45:44:44:55:67
do
    ! result=`$openmano sdn-controller-edit $sdn -f --"${edit}"` &&
        echo  "FAIL" && echo "    $result" && _exit 1
done
echo OK

printf "%-50s" "SDN-controller list:"
! result=`$openmano sdn-controller-list` &&
    echo  "FAIL" && echo "    $result" && _exit 1
for verbose in "" -v -vv -vvv
do
    ! result=`$openmano sdn-controller-list "$sdn" $verbose` &&
        echo  "FAIL" && echo "    $result" && _exit 1
done
echo OK

printf "%-50s" "Add sdn to datacenter:"
! result=`$openmano datacenter-edit -f $DC --sdn-controller $SDN` &&
    echo "FAIL" && echo "    $result" && _exit 1 || echo OK

printf "%-50s" "Clear Port mapping:"
! result=`$openmano datacenter-sdn-port-mapping-clear -f $DC` &&
    echo "FAIL" && echo "    $result" && _exit 1 || echo OK

printf "%-50s" "Set Port mapping:"
! result=`$openmano datacenter-sdn-port-mapping-set -f $DC ${DIRmano}/sdn/sdn_port_mapping.yaml` &&
    echo "FAIL" && echo "    $result" && _exit 1 || echo OK

printf "%-50s" "List Port mapping:"
for verbose in "" -v -vv -vvv
do
    ! result=`$openmano datacenter-sdn-port-mapping-list "$DC" $verbose` &&
        echo  "FAIL" && echo "    $result" && _exit 1
done
echo OK

printf "%-50s" "Set again Port mapping:"
! result=`$openmano datacenter-sdn-port-mapping-set -f $DC ${DIRmano}/sdn/sdn_port_mapping.yaml` &&
    echo "FAIL" && echo "    $result" && _exit 1 || echo OK

printf "%-50s" "Clear again Port mapping:"
! result=`$openmano datacenter-sdn-port-mapping-clear -f $DC` &&
    echo "FAIL" && echo "    $result" && _exit 1 || echo OK

printf "%-50s" "Set again Port mapping:"
! result=`$openmano datacenter-sdn-port-mapping-set -f $DC ${DIRmano}/sdn/sdn_port_mapping.yaml` &&
    echo "FAIL" && echo "    $result" && _exit 1 || echo OK

printf "%-50s" "Remove datacenter sdn:"
! result=`$openmano datacenter-edit -f $DC --sdn-controller null` &&
    echo "FAIL" && echo "    $result" && _exit 1 || echo OK

printf "%-50s" "Negative list port mapping:"
result=`$openmano datacenter-sdn-port-mapping-list $DC` &&
    echo "FAIL" && echo "    $result" && _exit 1 || echo OK

printf "%-50s" "Add again datacenter sdn:"
! result=`$openmano datacenter-edit -f $DC --sdn-controller $SDN` &&
    echo "FAIL" && echo "    $result" && _exit 1 || echo OK

printf "%-50s" "Empty list port mapping:"
! [[ `$openmano datacenter-sdn-port-mapping-list $DC | wc -l` -eq 6 ]] &&
    echo "FAIL" && _exit 1 || echo OK

printf "%-50s" "Set again Port mapping:"
! result=`$openmano datacenter-sdn-port-mapping-set -f $DC ${DIRmano}/sdn/sdn_port_mapping.yaml` &&
    echo "FAIL" && echo "    $result" && _exit 1 || echo OK

_exit 0

