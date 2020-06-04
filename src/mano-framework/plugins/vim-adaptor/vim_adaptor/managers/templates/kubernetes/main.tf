provider "kubernetes" {
  host = "${var.host}"
  token = "${var.token}"
  insecure = true
}