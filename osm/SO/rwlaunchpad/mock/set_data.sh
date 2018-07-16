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

#
# This script posts descriptor data (NSD, VNFD, VLD) to the RESTConf server
#
# Provide the RESTConf hostname as the argument or default to localhost
#

if [ $# -eq 0 ] ; then
    HOST=localhost
else
    HOST=$1
fi

echo "Posting descriptor data to $HOST"


#for descriptor in nsd vnfd vld

for descriptor in nsd vnfd
do
    echo "Assigning data to descriptor \"$descriptor\""

    curl --user admin:admin \
        -H "Content-Type: application/vnd.yang.data+json" \
        -X POST \
        -d @data/${descriptor}_catalog.json \
        http://$HOST:8008/api/running/$descriptor-catalog/ -v

done

for rectype in ns
do
    echo "Assigning data to instance config \"$rectype\""

    curl --user admin:admin \
        -H "Content-Type: application/vnd.yang.data+json" \
        -X POST \
        -d @data/${rectype}-instance-config.json \
        http://$HOST:8008/api/running/$rectype-instance-config/ -v

done

