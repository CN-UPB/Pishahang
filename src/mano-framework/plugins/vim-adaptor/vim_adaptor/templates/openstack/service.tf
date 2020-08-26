# Per-service virtual network
resource "openstack_networking_network_v2" "service_network" {
  name = "{{ service_instance_id }}"
  admin_state_up = "true"
}
