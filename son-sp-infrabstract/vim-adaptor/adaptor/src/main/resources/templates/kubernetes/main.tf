provider "kubernetes" {
  load_config_file = "false"

  host = "{{ endpoint }}"

  token = "{{ token }}"
  insecure = true
}