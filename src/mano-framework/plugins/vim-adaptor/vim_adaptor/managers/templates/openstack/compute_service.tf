{% for vdu in descriptor.virtual_deployment_units %}

#Image details
resource "openstack_images_image_v2" "image" {
  name = "{{ descriptor.name }}"
  image_source_url = "{{vdu.vm_image}}"
  disk_format = "{{ vdu.vm_image_format }}"
  container_format = "bare"
}

#Creating a compute flavor
resource "openstack_compute_flavor_v2" "flavor" {
  name  = "my-flavor"   #  unique name for the flavor.
  ram   = "{{ vdu.resource_requirements.memory.size }}"        #  amount of RAM to use, in megabytes
  vcpus = "{{ vdu.resource_requirements.cpu.vcpus }}"           #  number of virtual CPUs to use
  disk  = "{{ vdu.resource_requirements.storage.size }}"          #  amount of disk space in gigabytes
}

# Creating a openstack compute with an image id
resource "openstack_compute_instance_v2" "{{vdu.id}}-{{}}" {
  name            = "{{ descriptor.name }}" #name of image with count, if more than one.
  image_id        = "${openstack_images_image_v2.image.id}"#"7cd3f630-7c1b-4cc9-8f5c-3026e7fe2f59"
  image_name      = "${openstack_images_image_v2.image.name}"
  flavor_id       = "${openstack_compute_flavor_v2.flavor.id}"
  security_groups = ["default"] 
  # key_pair        = "${openstack_compute_keypair_v2.terraform.name}"
  user_data       = "#cloud-config\nhostname: pish.example.com\nfqdn: pish.example.com" #Cloud-Init
  #count           = 2 #number of duplicates

  #Meta-Information about the instance
  metadata = {
    name = "{{ descriptor.name }}"
    author = "{{ descriptor.author }}"
    vendor = "{{ descriptor.vendor }}"
    version = "{{ descriptor.version }}"
    description = "{{ descriptor.description }}"
    descriptor_version = "{{ descriptor.descriptor_version }}"
  }

  network {
    name = "public"
  }
}

{% endfor %}