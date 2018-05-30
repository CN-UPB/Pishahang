provider "kubernetes" {
  host = "{{ endpoint }}"

  token = "{{ token }}"
  insecure = true
}