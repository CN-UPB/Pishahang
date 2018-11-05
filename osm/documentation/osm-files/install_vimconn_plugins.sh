#!/bin/bash

# Get IP addresses of Resource Orchestrator and Service Orchestrator
SO_IP=$(lxc exec SO-ub ifconfig eth0 | grep 'inet addr' | cut -d: -f2 | awk '{print $1}')
RO_IP=$(lxc exec RO ifconfig eth0 | grep 'inet addr' | cut -d: -f2 | awk '{print $1}')

# Add information to bashrc to be able to use osmclient
echo "export OSM_HOSTNAME=$SO_IP" >> ~/.bashrc
echo "export OSM_RO_HOSTNAME=$RO_IP" >> ~/.bashrc
source ~/.bashrc

# Install required libraries for Python OpenStack API
pip install python-keystoneclient
lxc exec RO pip install python-keystoneclient
lxc exec RO pip install --user python-neutronclient
lxc exec RO pip uninstall websocket-client
lxc exec RO pip install -Iv websocket-client==0.32.0
lxc exec RO pip install kubernetes docker

# Install vimconn-Plugins for OSM
lxc file push ./vimconn_kubernetes.py RO/usr/lib/python2.7/dist-packages/osm_ro/vimconn_kubernetes.py
lxc file delete RO/usr/lib/python2.7/dist-packages/osm_ro/vimconn_openstack.py
lxc file push ./vimconn_openstack.py RO/usr/lib/python2.7/dist-packages/osm_ro/vimconn_openstack.py
# Restart RO to enable vimconn-Plugin changes
lxc exec RO service osm-ro restart
