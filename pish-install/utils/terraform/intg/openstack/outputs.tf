resource "template_file" "inventory" {
  template = "${file("inventory.tpl")}"
  vars {
    jk_host = "${join("\n",template_file.jk_hosts.*.rendered)}"
    intsrv_host = "${join("\n",template_file.intsrv_hosts.*.rendered)}"
  }
}

output "inventory" {
  value = "${template_file.inventory.rendered}"
}
