"""
Copyright (c) 2017 Pishahang
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of Pishahang, nor the names of its contributors
may be used to endorse or promote products derived from this software
without specific prior written permission.
"""

import logging
from uuid import UUID

from appcfg import get_config
from mongoengine import DoesNotExist, connect

from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin
from vim_adaptor.exceptions import (
    TerraformException,
    VimConnectionError,
    VimNotFoundException,
)
from vim_adaptor.models.vims import (
    AwsVimSchema,
    BaseVim,
    KubernetesVim,
    KubernetesVimSchema,
    OpenStackVim,
    OpenStackVimSchema,
    VimType,
)
from vim_adaptor.util import create_completed_response, create_error_response
from vim_adaptor.managers import factory as manager_factory
from vim_adaptor.models.function import FunctionInstance

logging.basicConfig(level=logging.INFO)
logging.getLogger("manobase:plugin").setLevel(logging.INFO)
logging.getLogger("amqpstorm.channel").setLevel(logging.ERROR)

LOG = logging.getLogger("plugin:vim-adaptor")
LOG.setLevel(logging.DEBUG)

config = get_config(__name__)


class VimAdaptor(ManoBasePlugin):
    """
    Vim Adaptor main class. Instantiate this class to run the Vim Adaptor.
    """

    def __init__(self, *args, **kwargs):
        # Connect to MongoDB
        LOG.debug("Connecting to MongoDB at %s", config["mongo"])
        connect(host=config["mongo"])
        LOG.info("Connected to MongoDB")

        kwargs.update({"version": "0.1.0", "start_running": False})
        super().__init__(*args, **kwargs)

    def declare_subscriptions(self):
        super().declare_subscriptions()
        # VIM Management
        self.conn.register_async_endpoint(
            self.add_vim, "infrastructure.management.compute.add"
        )
        self.conn.register_async_endpoint(
            self.delete_vim, "infrastructure.management.compute.remove"
        )
        self.conn.register_async_endpoint(
            self.list_vims, "infrastructure.management.compute.list"
        )
        # Instantiation
        self.conn.register_async_endpoint(
            self.prepare_infrastructure, "infrastructure.service.prepare"
        )
        self.conn.register_async_endpoint(
            self.deploy_kubernetes_function, "infrastructure.cloud_service.deploy"
        )
        self.conn.register_async_endpoint(
            self.deploy_openstack_function, "infrastructure.function.deploy"
        )

        # Termination
        self.conn.register_async_endpoint(
            self.remove_service, "infrastructure.service.remove"
        )

    def on_lifecycle_start(self, message: Message):
        super().on_lifecycle_start(message)
        LOG.info("VIM Adaptor started.")

    def add_vim(self, message: Message):
        payload = message.payload
        if "type" not in payload:
            return create_error_response('No "type" field was provided.')

        vim_type = payload["type"]
        if vim_type not in [t.value for t in VimType]:
            return create_error_response(
                'The "type" field must be one of {}. Got {}'.format(VimType, type)
            )

        if vim_type == VimType.OPENSTACK.value:
            schema = OpenStackVimSchema()
        elif vim_type == VimType.KUBERNETES.value:
            schema = KubernetesVimSchema()
        elif vim_type == VimType.AWS.value:
            schema = AwsVimSchema()

        vim, errors = schema.load(payload)
        if len(errors) > 0:
            return create_error_response(str(errors))

        # Try to get the resource utilization, fail if it does not work
        try:
            vim.get_resource_utilization()
        except NotImplementedError:
            pass
        except VimConnectionError as e:
            return create_error_response(str(e))

        vim.save()
        return create_completed_response({"id": str(vim.id)})

    def list_vims(self, message: Message):
        vims = []
        for vim in BaseVim.objects():
            try:
                resource_utilization = vim.get_resource_utilization()
            except VimConnectionError:
                resource_utilization = {
                    "core_total": 0,
                    "core_used": 0,
                    "memory_total": 0,
                    "memory_used": 0,
                }

            # TODO: Remove this once get_resource_utilization is implemented for all vim types
            except NotImplementedError:
                resource_utilization = {
                    "core_total": 4,
                    "core_used": 0,
                    "memory_total": 32000,
                    "memory_used": 0,
                }

            vims.append(
                {
                    "vim_uuid": str(vim.id),
                    "vim_name": vim.name,
                    "vim_country": vim.country,
                    "vim_city": vim.city,
                    "vim_type": "Kubernetes" if vim.type == "kubernetes" else vim.type,
                    **resource_utilization,
                }
            )

        return vims

    def delete_vim(self, message: Message):
        payload = message.payload
        if "id" not in payload:
            return create_error_response(
                'The request message does not contain an "id" field.'
            )

        id = payload["id"]

        try:
            UUID(id)
        except ValueError:
            return create_error_response('Invalid UUID "{}"'.format(id))

        try:
            vim = BaseVim.objects(id=id).get()
        except DoesNotExist:
            return create_error_response("No VIM with id {} exists".format(id))

        vim.delete()
        return create_completed_response()

    def prepare_infrastructure(self, message: Message):
        # TODO What exactly should this do?
        return create_completed_response()

    def deploy_kubernetes_function(self, message: Message):
        payload = message.payload

        try:
            vim = KubernetesVim.get_by_id(payload["vim_uuid"])
            manager = manager_factory.create_manager(
                "kubernetes",
                vim=vim,
                function_instance_id=payload["csd"]["instance_uuid"],
                function_id=payload["csd"]["uuid"],
                service_instance_id=payload["service_instance_id"],
                descriptor=payload["csd"],
            )
            return create_completed_response({"csr": manager.deploy()})
        except (VimNotFoundException, TerraformException) as e:
            return create_error_response(str(e))

    def deploy_openstack_function(self, message: Message):
        payload = message.payload

        try:
            vim = OpenStackVim.get_by_id(payload["vim_uuid"])
            manager = manager_factory.create_manager(
                "openstack",
                vim=vim,
                function_instance_id=payload["vnfd"]["instance_uuid"],
                function_id=payload["vnfd"]["uuid"],
                service_instance_id=payload["service_instance_id"],
                descriptor=payload["vnfd"],
            )
            manager.deploy()
            return create_completed_response()
        except (VimNotFoundException, TerraformException) as e:
            return create_error_response(str(e))

    def remove_service(self, message: Message):
        service_instance_id = message.payload["instance_uuid"]
        LOG.info("Removing service %s", service_instance_id)

        try:
            for function_instance in FunctionInstance.objects(
                service_instance_id=service_instance_id
            ):
                manager_factory.get_manager(function_instance.id).destroy()

            return create_completed_response()
        except TerraformException as e:
            return create_error_response(str(e))


def main():
    VimAdaptor()


if __name__ == "__main__":
    main()
