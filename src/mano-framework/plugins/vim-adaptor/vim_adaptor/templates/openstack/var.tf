variable username {
    description = "The Username to login with."
    type = string
}

variable tenant_id {
    description = "The ID of the Tenant (Identity v2) or Project (Identity v3) to login with."
    type = string
}

variable password {
    description = "The Password to login with."
    type = string
}

variable auth_url {
    description = "The Identity authentication URL."
    type = string
}

variable external_network_id {
    description = "The ID of the public network"
    type = string
}

variable external_router_id {
    description = "The ID of a router that is connected to the public network"
    type = string
}
