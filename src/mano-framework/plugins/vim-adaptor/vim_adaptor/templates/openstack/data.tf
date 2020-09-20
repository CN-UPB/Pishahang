# Retrieve the shared default IPv4 subnet pool
data "openstack_networking_subnetpool_v2" "IPv4" {
  shared = true
  is_default = true
  ip_version = 4
}

# Retrieve the shared default IPv6 subnet pool
data "openstack_networking_subnetpool_v2" "IPv6" {
  shared = true
  is_default = true
  ip_version = 6
}
