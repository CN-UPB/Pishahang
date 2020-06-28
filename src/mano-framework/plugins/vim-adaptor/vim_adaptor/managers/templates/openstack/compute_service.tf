{% for vdu in descriptor.virtual_deployment_units %}

#Image details
resource "openstack_images_image_v2" "image" {
  {% if vdu.name != null %}
    name = "{{ vdu.name }}"
  {% endif %}

  {% if vdu.vm_image != null %}
    image_source_url = "{{vdu.vm_image}}"
  {% endif %}

  {% if vdu.vm_image_format != null %}
    disk_format = "{{ vdu.vm_image_format }}"
  {% endif %}
  
  {% if vdu.vm_image_format != null %}
    container_format = "{{ vdu.vm_image_format }}"
  {% endif %}
}

#Creating a compute flavor
resource "openstack_compute_flavor_v2" "flavor" {
  name  = "flavor"-{{ vdu.id }}   #  unique name for the flavor.
  #flavor_id = "${openstack_images_image_v2.image.id}"
  {% if vdu.resource_requirements.memory.size != null %}
    ram   = "{{ vdu.resource_requirements.memory.size }}"        #  amount of RAM to use, in megabytes
  {% endif %}

  {% if vdu.resource_requirements.cpu.vcpus != null %}
    vcpus = "{{ vdu.resource_requirements.cpu.vcpus }}"           #  number of virtual CPUs to use
  {% endif %}

  {% if vdu.resource_requirements.storage.size != null %}
    disk  = "{{ vdu.resource_requirements.storage.size }}"          #  amount of disk space in gigabytes
  {% endif %}
}

# Creating a openstack compute with an image id
resource "openstack_compute_instance_v2" "{{ vdu.id }}-{{ instance_uuid }}" {
  name            = "{{ vdu.id }}-{{ instance_uuid }}"
  image_id        = "${openstack_images_image_v2.image.id}"
  image_name      = "${openstack_images_image_v2.image.name}"
  flavor_id       = "${openstack_compute_flavor_v2.flavor.id}"
  security_groups = ["default"] 
  # key_pair        = "${openstack_compute_keypair_v2.terraform.name}"

  {% connection in vdu.connection_points %}
    connection {
        {% if connection.id != null %}
          id = "{ connection.id }"
        {% endif %}
        {% if connection.type != null%}
          type = "{ connection.type }"
        {% endif %}

        {% if connection.interface != null%}
          interface = "{ connection.interface }"
        {% endif %}
    }
  {% endfor %}

  #Meta-Information about the instance
  metadata = {
    {% if vdu.id != null %}
      id = "{{ vdu.id }}"
    {% endif %}

    {% if vdu.description != null %}
      description = "{{ vdu.description }}"
    {% endif %}
  }

  network {
    name = "public"
  }
}
{% endfor %}