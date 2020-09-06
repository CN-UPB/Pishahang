# Per-service virtual network
resource "openstack_networking_network_v2" "service_network" {
  name = "service-{{ service_instance_id }}"
  admin_state_up = "true"
}

# VM images
{% for image in details.vm_images %}
resource "openstack_images_image_v2" "image-{{ loop.index }}" {
  name = "{{ image.id }}"

  image_source_url = "{{ image.url }}"
  disk_format = "{{ image.format }}"
  container_format = "bare" # https://docs.openstack.org/glance/ussuri/user/formats.html#container-format

  properties = {
    service = "{{ service_instance_id }}"
  }
}
{% endfor %}
