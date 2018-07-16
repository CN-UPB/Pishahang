#!/bin/bash

##
# Copyright 2017 Telefónica Investigación y Desarrollo, S.A.U.
# This file is part of OSM
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
##

# Author: Alfonso Tierno (alfonso.tiernosepulveda@telefonica.com)

description="It creates a new lxc container, installs RO from a concrete commit and executes validation tests.\
 An openvim in test mode is installed and used to validate"

usage(){
    echo -e "usage: ${BASH_SOURCE[0]} CONTAINER\n ${description}"
    echo -e "  CONTAINER is the name of the container to be created. By default test1"\
            "Warning! if a container with the same name exists, it will be deleted"
    echo -e "  You must also supply at TEST_RO_COMMIT envioronmental variable with the git command"\
            "to clone the version under test. It can be copy paste from gerrit. Examples:\n"\
            " TEST_RO_COMMIT='git fetch https://osm.etsi.org/gerrit/osm/RO refs/changes/40/5540/1 && git checkout FETCH_HEAD'\n"\
            " TEST_RO_COMMIT='git checkout v3.0.1'"
    echo -e "  You can provide TEST_RO_GIT_URL, by default https://osm.etsi.org/gerrit/osm/RO is used"
    echo -e "  You can provide TEST_RO_CONTAINER instead of by parameter, by default test1"
    echo -e "  You can provide TEST_RO_CUSTOM, with a command for container customization, by default nothing."
}

[ "$1" = "--help" ] || [ "$1" = "-h" ] && usage && exit 0

[[ -z "$TEST_RO_COMMIT" ]] && echo 'provide a TEST_RO_COMMIT variable. Type --help for more info' >&2 && exit 1
[[ -z "$TEST_RO_GIT_URL" ]] && TEST_RO_GIT_URL="https://osm.etsi.org/gerrit/osm/RO"

[ -n "$1" ] && TEST_RO_CONTAINER="$1"
[[ -z "$TEST_RO_CONTAINER" ]] && TEST_RO_CONTAINER=test1

instance_name=3vdu_2vnf

function echo_RO_log(){
    # echo "LOG DUMP:" >&2 && lxc exec "$TEST_RO_CONTAINER" -- tail -n 150 /var/log/osm/openmano.log >&2
    echo -e "\nFAILED" >&2
}

function lxc_exec(){
    if ! lxc exec "$TEST_RO_CONTAINER" --env OPENMANO_TENANT=osm --env OPENMANO_DATACENTER=local-openvim \
        --env OPENVIM_TENANT="$OPENVIM_TENANT" -- bash -c "$*"
    then
        echo "ERROR on command '$*'" >&2
        echo_RO_log
        exit 1
    fi
}

function wait_until_deleted(){
    wait_active=0
    while lxc_exec RO/test/local/openvim/openvim vm-list | grep -q -e ${instance_name} ||
          lxc_exec RO/test/local/openvim/openvim net-list | grep -q -e ${instance_name}
    do
        echo -n "."
        [ $wait_active -gt 90 ] &&  echo "timeout waiting VM and nets deleted at VIM" >&2 && echo_RO_log && exit 1
        wait_active=$((wait_active + 1))
        sleep 1
    done
    echo
}

lxc delete "$TEST_RO_CONTAINER" --force 2>/dev/null && echo "container '$TEST_RO_CONTAINER' deleted"
lxc launch ubuntu:16.04 "$TEST_RO_CONTAINER"
sleep 10
[[ -n "$TEST_RO_CUSTOM" ]] && ${TEST_RO_CUSTOM}
lxc_exec ifconfig eth0 mtu 1446  # Avoid problems when inside an openstack VM that normally limit MTU do this value
lxc_exec git clone "$TEST_RO_GIT_URL"
lxc_exec git -C RO status
lxc_exec "cd RO && $TEST_RO_COMMIT"

# TEST INSTALL
lxc_exec RO/scripts/install-openmano.sh --noclone --force -q --updatedb
sleep 10
lxc_exec openmano tenant-create osm
lxc_exec openmano tenant-list

# TEST database migration
lxc_exec ./RO/database_utils/migrate_mano_db.sh 20
lxc_exec ./RO/database_utils/migrate_mano_db.sh
lxc_exec ./RO/database_utils/migrate_mano_db.sh 20
lxc_exec ./RO/database_utils/migrate_mano_db.sh

# TEST instantiate with a fake local openvim
lxc_exec ./RO/test/basictest.sh -f --insert-bashrc --install-openvim reset add-openvim create delete


# TEST instantiate with a fake local openvim 2
lxc_exec ./RO/test/test_RO.py deploy -n mgmt -t osm -i cirros034 -d local-openvim --timeout=30 --failfast
lxc_exec ./RO/test/test_RO.py vim  -t osm  -d local-openvim --timeout=30 --failfast

sleep 10
echo "TEST service restart in the middle of a instantiation/deletion"
OPENVIM_TENANT=`lxc_exec RO/test/local/openvim/openvim tenant-list`
OPENVIM_TENANT=${OPENVIM_TENANT%% *}

lxc_exec openmano vnf-create RO/vnfs/examples/v3_3vdu_vnfd.yaml --image-name=cirros034
lxc_exec openmano scenario-create RO/scenarios/examples/v3_3vdu_2vnf_nsd.yaml
wait_until_deleted
test_number=0
while [ $test_number -lt 5 ] ; do
    echo test ${test_number}.0 test instantiation recovering
    lxc_exec openmano instance-scenario-create --name ${instance_name} --scenario osm_id=3vdu_2vnf_nsd";"service osm-ro stop
    sleep 5
    lxc_exec service osm-ro start
    sleep 10
    # wait until all VM are active
    wait_active=0
    while [ `lxc_exec openmano instance-scenario-list ${instance_name} | grep ACTIVE | wc -l` -lt 7 ] ; do
        echo -n "."
        [ $wait_active -gt 90 ] &&  echo "timeout waiting VM active" >&2 && echo_RO_log && exit 1
        wait_active=$((wait_active + 1))
        sleep 1
    done
    echo

    # Due to race condition the VIM request can be processed without getting the response by RO
    # resulting in having some VM or net at VIM not registered by RO. If this is the case need to be deleted manually
    vim_vms=`lxc_exec RO/test/local/openvim/openvim vm-list | grep ${instance_name} | awk '{print $1}'`
    for vim_vm in $vim_vms ; do
        if ! lxc_exec openmano instance-scenario-list ${instance_name} | grep -q $vim_vm ; then
            echo deleting VIM vm $vim_vm
            lxc_exec RO/test/local/openvim/openvim vm-delete -f $vim_vm
        fi
    done
    vim_nets=`lxc_exec RO/test/local/openvim/openvim net-list | grep ${instance_name} | awk '{print $1}'`
    for vim_net in $vim_nets ; do
        if ! lxc_exec openmano instance-scenario-list ${instance_name} | grep -q $vim_net ; then
            echo deleting VIM net $vim_net
            lxc_exec RO/test/local/openvim/openvim net-delete -f $vim_net
        fi
    done

    # delete first VIM VM and wait until RO detects it
    echo test ${test_number}.1 test refresh VM VIM status deleted
    OPENVIM_VM=`lxc_exec RO/test/local/openvim/openvim vm-list`
    OPENVIM_VM=${OPENVIM_VM%% *}
    lxc_exec RO/test/local/openvim/openvim vm-delete -f $OPENVIM_VM
    wait_active=0
    while ! lxc_exec openmano instance-scenario-list ${instance_name} | grep -q DELETED ; do
        echo -n "."
        [ $wait_active -gt 90 ] &&  echo "timeout waiting RO get VM status as DELETED" >&2 && echo_RO_log && exit 1
        wait_active=$((wait_active + 1))
        sleep 1
        ACTIVE=`lxc_exec openmano instance-scenario-list ${instance_name} | grep ACTIVE | wc -l`
    done
    echo

    # TEST service restart in the middle of a instantiation deletion
    echo test ${test_number}.2 test isntantiation deletion recovering
    lxc_exec openmano instance-scenario-delete ${instance_name} -f";"service osm-ro stop
    sleep 5
    lxc_exec service osm-ro start
    sleep 10
    # wait until all VM are deteled at VIM
    wait_until_deleted

    test_number=$((test_number + 1))
done
echo "DONE"


