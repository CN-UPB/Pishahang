#
# AUTH
os_username   = "son-demo"
os_tenantname = "son-demo"
os_password   = "S0n-d3m0"
os_auth_url   = "http://172.31.6.4:5000/v2.0"

# VM INSTANCE
vm_name     = "vm"
os_img_id   = "7129fb44-a239-458c-a45f-f93342ed458c"  # Ub14 trusty cld img (SAL)
#os_img_id  = "fed16665-bed0-46f8-8a95-42801ca9753d"  # Ub16 xenial cld img (SAL)
#os_img_id  = "b7ae5d8c-8c65-4411-8251-1985d714c2a7"  # Cen7 cld img (SAL)
os_flv_id   = "2"  # '1'-tiny '2'-m1.small '3'-m1.medium '4'-m1.large '5'-
#os_region"  = "" 
os_sec_grp = "son-demo-secgrp" 
os_key_pair = "son-ift-ptin" 

# NETW
#internal_network_id = "ae8475b3-a9e0-426f-9798-1626801da900"  # DEV NETW
internal_network_id = "cffedbd8-e2a5-4cc3-92f9-0ce5259e4d31" # DEMO NETW
internal_network_name = "son-dev-netw" 

# FLOATING IP
os_fip_pool = "admin_floating_net" 

# DISTRO
distro = "trusty"  # distros = "trusty | xenial | centos7"

# APP LAYERs
#layer = "fe"  # layers = "fe | midtier | be"

# ENVIRONMENTS
env = "demo"  # environ = "int | qual | demo"

