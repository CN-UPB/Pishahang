variable user_name {
    description = "The Username to login with."
}

variable tenant_name {
    description = "The ID of the Tenant (Identity v2) or Project (Identity v3) to login with."
}

variable password {
    description = "(Optional) The Password to login with."
}

variable auth_url {
    description = "The Identity authentication URL."
}

variable region {
    description = "The region of the OpenStack cloud to use."
    default = "RegionOne"
}