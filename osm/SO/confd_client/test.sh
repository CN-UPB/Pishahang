#!/bin/bash

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

# This script tests the throughput of get operations.
# change iter and loop variables

NETCONF_CONSOLE_DIR=${RIFT_ROOT}/.install/usr/local/confd/bin

iter=100
loop=30

for i in `seq 1 $loop`;
do
    echo "Background script $i"
    ${NETCONF_CONSOLE_DIR}/netconf-console-tcp -s all --iter=$iter --get -x /opdata&
done

wait

total=$(($iter * $loop))
echo "Total number of netconf operations=$total"



