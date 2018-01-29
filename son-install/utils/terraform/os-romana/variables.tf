# AUTH
variable "os_username"   { }
variable "os_tenantname" { }
variable "os_password"   { }
variable "os_auth_url"   { }

# VM INSTANCE
variable "vm_name"     { }
variable "os_img_id"   { } 
#variable "os_img_id"  { }
#variable "os_img_id"  { }
variable "os_flv_id"   { }
#variable "os_region"  { }
variable "os_sec_grp"  { }
variable "os_key_pair" { }

# NETW
variable "internal_network_id"   { }
variable "internal_network_name" { }

# FLOATING IP
variable "os_fip_pool"  { }

# DISTRO
variable "distro" { }

# APP LAYERs
#variable "layer" { }

# ENVIRONMENTS
variable "env" { }
