variable "user_name"{
    description = "The Username to login with. If omitted, the OS_USERNAME environment variable is used."
    default = "pish"
}

variable "tenant_name"{
    description = "The ID of the Tenant (Identity v2) or Project (Identity v3) to login with. If omitted, the OS_TENANT_ID or OS_PROJECT_ID environment variables are used."
    default = "pishahang"
}

variable "password"{
    description = "(Optional) The Password to login with. If omitted, the OS_PASSWORD environment variable is used."
    default = "1234"
}

# variable "ssh_key_file" {
#     description = ""
#     default = "rsa.pem"
# }

variable "auth_url"{
    description = "(Optional; required if cloud is not specified) The Identity authentication URL. If omitted, the OS_AUTH_URL environment variable is used."
    default = "http://131.234.29.246/identity"
}

variable "region"{
    description = "The region of the OpenStack cloud to use."
    default = "RegionOne"
}