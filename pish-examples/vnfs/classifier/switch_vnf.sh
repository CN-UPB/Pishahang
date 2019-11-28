#!/usr/bin/env bash

sudo iptables -F
sudo iptables -t nat -F

sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination $1:$2
# sudo iptables -t nat -A POSTROUTING -p tcp -d 192.168.202.105 --dport 80 -j SNAT --to-source 192.168.202.103
# sudo iptables -t nat -L -n
sudo iptables -t nat -A POSTROUTING -j MASQUERADE