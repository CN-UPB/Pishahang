# TENANT AUTH
variable "os_auth_url" {default = "http://172.31.6.4:5000/v2.0"}
variable "os_tenant"   {default = "son-qual"}
variable "os_username" {default = "son-qual"}
variable "os_password" {default = "S0n-qu@l"}

# VM
variable "vm_name"     {default = "qual"}
variable "img_name"    {default = "trusty-cldimg"}
variable "flv_name"    {default = "m1.small"}
variable "sec_grp"     {default = "son-qual-secgrp"}
variable "key_pair"    {default = "son-ift-ptin"}

# NETW
variable "internal_network_name" {default = "son-qual-netw"}
variable "internal_network_id"   {default = "ffdf5f4f-eeee-49ac-ac34-ccaf814bfb84"}
variable "floatipnet"            {default = "admin_floating_net"}
#variable "floatipaddr"           {default = ""}

# LOCATION
#variable "region"            {default = "RegionOne"}
#variable "availability_zone" {default = "nova"}

# ENVIRONMENTs
variable "env"         {default = "qual"}

# DISTROs
variable "distro"      {default = "trusty"}

