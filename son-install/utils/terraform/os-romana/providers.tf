provider "openstack" {
    user_name   = "${var.os_username}"   # default OS_USERNAME    env var
    tenant_name = "${var.os_tenantname}" # default OS_TENANT_NAME env var
    password    = "${var.os_password}"   # default OS_PASSWORD    env var
    auth_url    = "${var.os_auth_url}"   # default OS_AUTH_URL    env var
    #token      = "${var.os_token}"      # default OS_AUTH_TOKEN  env var
}

