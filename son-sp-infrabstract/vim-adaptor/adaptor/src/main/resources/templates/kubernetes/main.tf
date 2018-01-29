provider "kubernetes" {
  host = "{{ endpoint }}"

  token = "{{ token }}"
  cluster_ca_certificate = <<EOF
{{ caCert }}
EOF
}