#!/bin/bash

gatewaynic=ens160
nic=(ens192 ens224 ens256 ens161 ens193 ens225 ens257 ens162)
ip=(172.16.21 172.16.22 172.16.23 172.16.24 172.16.25 172.16.26 172.16.27 172.16.28)
subnet=172.16.0.0/16

# Enable IPv4 forwarding
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward = 1" | tee /etc/sysctl.conf
sysctl -p

iptables -A FORWARD -o ens160 -s ${subnet} -m conntrack --ctstate NEW -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -t nat -F POSTROUTING
iptables -t nat -A POSTROUTING -o ens160 -j MASQUERADE
iptables-save | tee /etc/iptables.sav
printf "iptables-restore < /etc/iptables.sav
exit 0
" | tee /etc/rc.local

# Create bridge
ovs-vsctl add-br br-${gatewaynic}
ovs-vsctl set Bridge br-${gatewaynic} "protocols=OpenFlow13"
ovs-vsctl add-port br-${gatewaynic} ${gatewaynic}

# Connect OVS switch to network by assigning IP
ip addr flush dev ${gatewaynic}
dhclient br-${gatewaynic}
ip link set br-${gatewaynic} up

# Add default routing entry
ip route delete default
ip route add default dev br-${gatewaynic}

# Add core bridge
ovs-vsctl add-br br-core
ovs-vsctl set Bridge br-core "protocols=OpenFlow13"
ip link set up br-core

for (( i=0; i<${#nic[@]}; i++ ));
do
    bridge=br-${nic[$i]}

    # Create bridge
    ovs-vsctl add-br ${bridge}
    ovs-vsctl set Bridge ${bridge} "protocols=OpenFlow13"
    ovs-vsctl add-port ${bridge} ${nic[$i]}

    # Connect OVS switch to network by assigning IP
    ip addr flush dev ${nic[$i]}
    ip addr add ${ip[$i]}.1 dev ${bridge}
    ip link set ${bridge} up

    # Add default routing entry
    ip route delete ${ip[$i]}.0/24
    ip route add ${ip[$i]}.0/24 dev ${bridge}
done

# Add patch ports on br-core
for (( i=0; i<${#nic[@]}; i++ ));
do
    bridge=br-${nic[$i]}
    ovs-vsctl \
    -- add-port br-core patch-br-core-${bridge} \
    -- set interface patch-br-core-${bridge} type=patch options:peer=patch-${bridge}-br-core ofport_request=$(( ${i} + 1 ))
done

# Add patch ports for each bridge connected to physical NIC
for (( i=0; i<${#nic[@]}; i++ ));
do
    bridge=br-${nic[$i]}
    ovs-vsctl \
    -- add-port ${bridge} patch-${bridge}-br-core \
    -- set Interface patch-${bridge}-br-core type=patch options:peer=patch-br-core-${bridge} ofport_request=2
done

# Configure bridges connected to physical NIC to forward in both directions
for (( i=0; i<${#nic[@]}; i++ ));
do
    bridge=br-${nic[$i]}
    ovs-ofctl del-flows -OOpenFlow13 ${bridge}
    ovs-ofctl add-flow -OOpenFlow13 ${bridge} "table=0, priority=2, in_port=1 actions=output=2"
    ovs-ofctl add-flow -OOpenFlow13 ${bridge} "table=0, priority=2, in_port=2 actions=output=1"
done
