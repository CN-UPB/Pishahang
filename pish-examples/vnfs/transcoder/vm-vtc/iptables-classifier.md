<!-- http://jensd.be/343/linux/forward-a-tcp-port-to-another-ip-or-port-using-nat-with-iptables -->
<!-- For our setup to work, we need to add a DNAT and SNAT rule (Prerouting and Postrouting). The first one will make sure that the packet gets routed to the other host (ip: 10.2.2.2) and the second one will make sure that the source address of the packet is no longer the original one but the one of the machine who performed the NAT. That way, the packet will be sent back to it’s original source via the host which owns ip 10.1.1.1. -->


sudo iptables -t nat -A PREROUTING -p tcp --dport 9999 -j DNAT --to-destination 192.168.202.105:80
sudo iptables -t nat -A POSTROUTING -p tcp -d 192.168.202.105 --dport 80 -j SNAT --to-source 192.168.202.103
sudo iptables -t nat -L -n

----

curl 192.168.122.222:8080/switch?ip=192.168.122.53\&port=80

curl 192.168.122.222:8080/switch?ip=131.234.250.178\&port=31391