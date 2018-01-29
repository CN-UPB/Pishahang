resource "template_file" "inventory" {
  template = "${file("inventory.tpl")}"
  vars {
    env = "${var.env}"
    os_hosts = "${join("\n",template_file.os_hosts.*.rendered)}"
  }
}

output "inventory" {
  value = "${template_file.inventory.rendered}"
}
