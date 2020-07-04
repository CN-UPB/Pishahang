{% for vdu in descriptor.virtual_deployment_units %}
resource "openstack_images_image_v2" "{{ vdu.id }}" {
  name = "{{ function_id }}-{{ vdu.id }}"

  image_source_url = "{{vdu.vm_image}}"
  disk_format = "{{ vdu.vm_image_format }}"
  container_format = "bare" # https://docs.openstack.org/glance/ussuri/user/formats.html#container-format
}

resource "openstack_compute_flavor_v2" "{{ vdu.id }}" {
  name = "{{ function_instance_id }}-{{ vdu.id }}"

  ram = "{{ vdu.resource_requirements.memory.size }}" #  amount of RAM to use, in megabytes
  vcpus = "{{ vdu.resource_requirements.cpu.vcpus }}" #  number of virtual CPUs to use

  {% if vdu.resource_requirements.storage.size %}
    disk = "{{ vdu.resource_requirements.storage.size }}" #  amount of disk space in gigabytes
  {% endif %}
}

resource "openstack_compute_instance_v2" "{{ vdu.id }}" {
  name            = "{{ function_instance_id }}-{{ vdu.id }}"
  image_id        = openstack_images_image_v2.{{ vdu.id }}.id
  image_name      = openstack_images_image_v2.{{ vdu.id }}.name
  flavor_id       = openstack_compute_flavor_v2.{{ vdu.id }}.id
  security_groups = ["default"] 
  # key_pair        = "${openstack_compute_keypair_v2.terraform.name}"

  metadata = {
    {% if vdu.id %}
      id = "{{ vdu.id }}"
    {% endif %}

    {% if vdu.description %}
      description = "{{ vdu.description }}"
    {% endif %}
  }

  network {
    name = "public"
  }
}
{% endfor %}