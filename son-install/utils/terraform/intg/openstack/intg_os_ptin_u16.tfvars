# TENANT AUTH
os_auth_url" {default = "http://172.31.6.4:5000/v2.0"
os_tenant"   {default = "son-int"
os_username" {default = "son-int"
os_password" {default = "S0n-1nt"

# VM
vm_name  = "int"
img_name = "xenial-cldimg"
flv_name = "m1.small"
sec_grp  = "son-int-secgrp"
key_pair = "son-ift-ptin"
key_path = "~/.ssh/son-ift-ptin.pem"

# NETW
internal_network_name = "son-int-netw"
internal_network_id   = "a4177ab4-55d5-4c53-a0b0-f0bd95898c89" # INTG NETW
#internal_network_id  = "ffdf5f4f-eeee-49ac-ac34-ccaf814bfb84" # QUAL NETW
#internal_network_id  = "cffedbd8-e2a5-4cc3-92f9-0ce5259e4d31" # DEMO NETW

# FIP
floatipnet    = "admin_floating_net"
# floatipaddr = ""

# LOCATION
#region            = "RegionOne"
#availability_zone = "nova"

# TF REMOTE-EXEC
user_distro = "ubuntu"

