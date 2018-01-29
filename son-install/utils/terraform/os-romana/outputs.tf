resource "template_file" "inventory" {
  template = "${file("inventory.tpl")}"
  vars {
    env = "${var.env}"
    ctrl_hosts = "${join("\n",template_file.ctrl_hosts.*.rendered)}"
    comp_hosts = "${join("\n",template_file.comp_hosts.*.rendered)}"
  }
}

output "inventory" {
  value = "${template_file.inventory.rendered}"
}

