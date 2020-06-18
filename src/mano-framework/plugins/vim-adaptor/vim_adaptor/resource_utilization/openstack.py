from novaclient.client import Client

import vim_adaptor.models.vims as vims
from vim_adaptor.exceptions import VimConnectionError
from keystoneauth1.exceptions.http import Unauthorized


def get_resource_utilization(vim: vims.OpenStackVim):
    try:
        nova = Client(
            version="2",
            username=vim.username,
            password=vim.password,
            project_id=vim.tenant.id,
            auth_url="http://{}:5000/".format(vim.address),
            timeout=5,
        )
        limits = nova.limits.get(tenant_id=vim.tenant.id).to_dict()["absolute"]

        resource_utilization = {
            "core_total": limits["maxTotalCores"],
            "core_used": limits["totalCoresUsed"],
            "memory_total": limits["maxTotalRAMSize"],
            "memory_used": limits["totalRAMUsed"],
        }

        return resource_utilization

    except Unauthorized:
        raise VimConnectionError(
            "Authorization error. Please check the tenant id, username, and password."
        )
    except Exception as e:
        raise VimConnectionError(str(e))
