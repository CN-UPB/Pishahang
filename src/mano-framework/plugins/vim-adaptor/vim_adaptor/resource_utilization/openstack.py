from keystoneauth1.exceptions.http import Unauthorized
from keystoneauth1.loading import get_plugin_loader
from keystoneauth1.session import Session
from novaclient.client import Client

import vim_adaptor.models.vims as vims
from vim_adaptor.exceptions import VimConnectionError


def get_resource_utilization(vim: vims.OpenStackVim):
    try:
        nova = Client(
            version="2",
            session=Session(
                auth=get_plugin_loader("password").load_from_options(
                    auth_url="http://{}/identity".format(vim.address),
                    username=vim.username,
                    password=vim.password,
                    user_domain_id="default",
                    project_id=vim.tenant.id,
                ),
                timeout=5,
            ),
        )
        limits = nova.limits.get(tenant_id=vim.tenant.id).to_dict()["absolute"]

        return {
            "cores_total": limits["maxTotalCores"],
            "cores_used": limits["totalCoresUsed"],
            "memory_total": limits["maxTotalRAMSize"],
            "memory_used": limits["totalRAMUsed"],
        }

    except Unauthorized:
        raise VimConnectionError(
            "Authorization error. Please check the tenant id, username, and password."
        )
    except Exception as e:
        raise VimConnectionError(str(e))
