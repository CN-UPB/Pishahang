[all:vars]
# Environment: INTEGRATION | QUALIFICATION | DEMONSTRATION
env=inte

# Network to configure access
network=172.31.6.0

# Netmask to configure access
netmask=24

[jk]
${jk_host}

[intsrv]
${intsrv_host}

[sp4int:children]
jk
intsrv
