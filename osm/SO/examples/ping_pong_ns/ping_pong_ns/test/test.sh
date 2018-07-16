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


pong_ip='14.0.0.2'
pong_port=18889

ping_ip='14.0.0.3'

ping_port=18888

if [ "$1" == "pong" ];
then
    if [ "$2" == "enable" ];
    then
	echo "enable pong"

	curl -D /dev/stdout \
	     -H "Accept: application/vnd.yang.data+xml" \
	     -H "Content-Type: application/vnd.yang.data+json" \
	     -X POST \
	     -d "{\"enable\":true}" \
	     http://${pong_ip}:${pong_port}/api/v1/pong/adminstatus/state
    fi
    if [ "$2" == "disable" ];
    then
    	echo "disable pong"
	
	curl -D /dev/stdout \
	     -H "Accept: application/vnd.yang.data+xml" \
	     -H "Content-Type: application/vnd.yang.data+json" \
	     -X POST \
	     -d "{\"enable\":false}" \
	     http://${pong_ip}:${pong_port}/api/v1/pong/adminstatus/state
    fi

    if [ "$2" == "server" ];
    then
	echo "set server"
	
	curl -D /dev/stdout \
	     -H "Accept: application/vnd.yang.data+xml" \
	     -H "Content-Type: application/vnd.yang.data+json" \
	     -X POST \
	     -d "{\"ip\":\"$3\", \"port\":$4}" \
	     http://${pong_ip}:${pong_port}/api/v1/pong/server
    fi

    echo ""
fi

if [ "$1" == "ping" ];
then
    if [ "$2" == "enable" ];
    then
	echo "enable ping"

	curl -D /dev/stdout \
	     -H "Accept: application/vnd.yang.data+xml" \
	     -H "Content-Type: application/vnd.yang.data+json" \
	     -X POST \
	     -d "{\"enable\":true}" \
	     http://${ping_ip}:${ping_port}/api/v1/ping/adminstatus/state
    fi
    if [ "$2" == "disable" ];
    then
	echo "disable ping"
	
	curl -D /dev/stdout \
	     -H "Accept: application/vnd.yang.data+xml" \
	     -H "Content-Type: application/vnd.yang.data+json" \
	     -X POST \
	     -d "{\"enable\":false}" \
	     http://${ping_ip}:${ping_port}/api/v1/ping/adminstatus/state
    fi
    echo ""

    if [ "$2" == "rate" ];
    then
	echo "disable ping"
	
	curl -D /dev/stdout \
	     -H "Accept: application/vnd.yang.data+xml" \
	     -H "Content-Type: application/vnd.yang.data+json" \
	     -X POST \
	     -d "{\"rate\":$3}" \
	     http://${ping_ip}:${ping_port}/api/v1/ping/rate
    fi
    echo ""

    if [ "$2" == "server" ];
    then
	echo "set server"
	
	curl -D /dev/stdout \
	     -H "Accept: application/vnd.yang.data+xml" \
	     -H "Content-Type: application/vnd.yang.data+json" \
	     -X POST \
	     -d "{\"ip\":\"$3\", \"port\":$4}" \
	     http://${ping_ip}:${ping_port}/api/v1/ping/server
    fi
    echo ""

    
fi

if [ "$1" == "stats" ];
then
    echo "ping stats:"
    curl http://${ping_ip}:${ping_port}/api/v1/ping/stats
    echo ""

    echo "pong stats:"
    curl http://${pong_ip}:${pong_port}/api/v1/pong/stats
    echo ""
fi

if [ "$1" == "config" ];
then
    echo "ping server:"
    curl http://${ping_ip}:${ping_port}/api/v1/ping/server
    echo ""
    echo "ping rate:"
    curl http://${ping_ip}:${ping_port}/api/v1/ping/rate
    echo ""
    echo "ping admin status:"
    curl http://${ping_ip}:${ping_port}/api/v1/ping/adminstatus/state
    echo ""
    echo "pong server:"
    curl http://${pong_ip}:${pong_port}/api/v1/pong/server
    echo ""
    echo "pong admin status:"
    curl http://${pong_ip}:${pong_port}/api/v1/pong/adminstatus/state
    echo ""
fi
