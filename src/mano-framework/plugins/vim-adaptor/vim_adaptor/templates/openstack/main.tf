# Configure the OpenStack Provider
provider "openstack" {
  auth_url    = var.auth_url
  user_name   = var.username
  password    = var.password
  tenant_id = var.tenant_id
  user_domain_id = "default"
}