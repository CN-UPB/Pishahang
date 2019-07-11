#
variable "intsrv_node_count" {
  default = 2
}

resource "openstack_compute_floatingip_v2" "fip" {
    region = ""
    pool = "${var.floatipnet}"
    count = "${var.intsrv_node_count}"
}
 
resource "openstack_compute_instance_v2" "intsrv" {
  count = "${var.intsrv_node_count}"
  region = ""
  name = "${var.vm_name}srv${format("%02d",count.index)}"
  image_name = "${var.img_name}"
  flavor_name = "${var.flv_name}"
  key_pair = "${var.key_pair}"
  security_groups = ["${var.sec_grp}"]
  #metadata {
  #    demo = "metadata"
  #}
  network {
      uuid = "${var.internal_network_id}"
      name = "${var.internal_network_name}"
      #fixed_ip = ""
  }
  floating_ip = "${element(openstack_compute_floatingip_v2.fip.*.address, count.index)}"
  #user_data = "${file("bootstrap-${distro}.sh")}"
  provisioner "remote-exec" {
    inline = [
      "bootstrap-${distro}.sh"
    ]
    connection {
        type = "ssh"
        user = "ubuntu"
        private_key = "${file("/home/centos/.ssh/son-ift-ptin.pem")}"
    }
  }
}

resource "template_file" "intsrv_hosts" {
  count = "${var.intsrv_node_count}"
#  location = "${var.placement}"
  template = "${file("hostname.tpl")}"
  vars {
    index = "${count.index + 1}"
    name  = "intsrv"
    env   = "int"
    extra = " ansible_host=${element(openstack_compute_floatingip_v2.fip.*.address, count.index)}"
  }
}

