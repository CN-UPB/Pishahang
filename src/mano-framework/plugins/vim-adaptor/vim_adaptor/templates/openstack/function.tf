# Get per-service virtual network
data "openstack_networking_network_v2" "service_network" {
  name = "service-{{ service_instance_id }}"
}

# Per-function-instance virtual network subnet
resource "openstack_networking_subnet_v2" "subnet" {
  name = "{{ descriptor.name }}-{{ function_instance_id }}-subnet"
  network_id = data.openstack_networking_network_v2.service_network.id
  subnetpool_id = data.openstack_networking_subnetpool_v2.IPv4.id
  prefix_length = 28 # 16 IPv4 adresses for the function instance subnet
}

{% for vdu in descriptor.virtual_deployment_units %}
  data "openstack_images_image_v2" "{{ vdu.id }}" {
    name = "{{ descriptor.vendor }}_{{ descriptor.name }}_{{ descriptor.version }}_{{ vdu.id }}"

    properties = {
      service = "{{ service_instance_id }}"
    }
  }

  resource "openstack_compute_flavor_v2" "{{ vdu.id }}" {
    name = "{{ function_instance_id }}_{{ descriptor.vendor }}_{{ descriptor.name }}_{{ descriptor.version }}_{{ vdu.id }}"
    is_public = false

    ram = "{{ vdu.resource_requirements.memory.size }}" #  amount of RAM to use, in megabytes
    vcpus = "{{ vdu.resource_requirements.cpu.vcpus }}" #  number of virtual CPUs to use

    {% if vdu.resource_requirements.storage.size %}
      disk = "{{ vdu.resource_requirements.storage.size }}" # minimum amount of disk space in gigabytes
    {% endif %}
  }


  {% for cp in vdu.connection_points %}
    resource "openstack_networking_port_v2" "{{ vdu.id }}-{{ cp.id }}" {
      name           = "{{ cp.id }}"
      network_id     = data.openstack_networking_network_v2.service_network.id
      admin_state_up = "true"

      fixed_ip {
        subnet_id = openstack_networking_subnet_v2.subnet.id
      }
    }
  {% endfor %}

  resource "openstack_compute_instance_v2" "{{ vdu.id }}" {
    name            = "{{ function_instance_id }}-{{ vdu.id }}"
    image_id        = data.openstack_images_image_v2.{{ vdu.id }}.id
    image_name      = data.openstack_images_image_v2.{{ vdu.id }}.name
    flavor_id       = openstack_compute_flavor_v2.{{ vdu.id }}.id
    security_groups = ["default"]

    metadata = {
      {% if vdu.id %}
        id = "{{ vdu.id }}"
      {% endif %}

      {% if vdu.description %}
        description = "{{ vdu.description }}"
      {% endif %}
    }

    {% for cp in vdu.connection_points %}
      network {
        port = openstack_networking_port_v2.{{ vdu.id }}-{{ cp.id }}.id
      }
    {% endfor %}
  }
{% endfor %}