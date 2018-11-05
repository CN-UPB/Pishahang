# Example flow rules and useful OVS debugging and development commands

ovs-ofctl del-flows -OOpenFlow13 br-core
# Send ARP replies VM1 and VM2
# SHA = hex of MAC
# SPA = hex of IP
ovs-ofctl add-flow -OOpenFlow13 br-core "table=0, dl_type=0x0806, nw_dst=172.16.21.1, actions=move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[], mod_dl_src:00:50:56:b8:90:fb, load:0x2->NXM_OF_ARP_OP[], move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[], move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[], load:0x005056b890fb->NXM_NX_ARP_SHA[], load:0xac101501->NXM_OF_ARP_SPA[], in_port"
ovs-ofctl add-flow -OOpenFlow13 br-core "table=0, dl_type=0x0806, nw_dst=172.16.22.1, actions=move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[], mod_dl_src:00:50:56:b8:1d:47, load:0x2->NXM_OF_ARP_OP[], move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[], move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[], load:0x005056b81d47->NXM_NX_ARP_SHA[], load:0xac101601->NXM_OF_ARP_SPA[], in_port"

# IPv4 connectivity VM1 and VM2
ovs-ofctl add-flow -OOpenFlow13 br-core "table=0, dl_type=0x0800, nw_src=172.16.21.0/24, nw_dst=172.16.22.0/24, actions=mod_dl_src=00:50:56:b8:1d:47, mod_dl_dst=00:50:56:b8:83:a4, dec_ttl, output=2"
ovs-ofctl add-flow -OOpenFlow13 br-core "table=0, dl_type=0x0800, nw_src=172.16.22.0/24, nw_dst=172.16.21.0/24, actions=mod_dl_src=00:50:56:b8:90:fb, mod_dl_dst=00:50:56:b8:e3:4f, dec_ttl, output=1"

# IPv4 VM1 to OS-VM on VM2 (OS floating IP in private nw)
ovs-ofctl add-flow -OOpenFlow13 br-core "table=0, dl_type=0x0800, nw_src=172.24.5.0/24, nw_dst=172.16.21.0/24, actions=mod_dl_src=00:50:56:b8:90:fb, mod_dl_dst=00:50:56:b8:e3:4f, dec_ttl, output=1"
ovs-ofctl add-flow -OOpenFlow13 br-core "table=0, dl_type=0x0800, nw_src=172.16.21.0/24, nw_dst=172.24.5.0/24, actions=mod_dl_src=00:50:56:b8:1d:47, mod_dl_dst=00:50:56:b8:83:a4, dec_ttl, output=2"
# IPv4 VM2 to OS-VM on VM1 (OS floating IP in private nw)
ovs-ofctl add-flow -OOpenFlow13 br-core "table=0, dl_type=0x0800, nw_src=172.24.4.0/24, nw_dst=172.16.22.0/24, actions=mod_dl_src=00:50:56:b8:1d:47, mod_dl_dst=00:50:56:b8:83:a4, dec_ttl, output=2"
ovs-ofctl add-flow -OOpenFlow13 br-core "table=0, dl_type=0x0800, nw_src=172.16.22.0/24, nw_dst=172.24.4.0/24, actions=mod_dl_src=00:50:56:b8:90:fb, mod_dl_dst=00:50:56:b8:e3:4f, dec_ttl, output=1"


# Reset behaviour to 'NORMAL' (automatic ARP replies and IP forwarding)
bridge_name=br-ens192
ovs-ofctl del-flows -OOpenFlow13 ${bridge_name}
ovs-ofctl add-flow -OOpenFlow13 ${bridge_name} "table=0, priority=0, actions=NORMAL"

# Get port-name-id-mapping
ovs-vsctl -- --columns=name,ofport list Interface

# Simulate packet
ovs-appctl ofproto/trace br-core in_port=2,dl_src=fe:16:3e:33:8b:d8,dl_dst=ff:ff:ff:ff:ff:ff,tcp,ip_src=172.16.22.2,ip_dst=172.16.21.2
