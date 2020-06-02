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
from vim_adaptor.models.vims import (
    AwsVimSchema,
    BaseVim,
    KubernetesVimSchema,
    OpenStackVimSchema,
    VimType,
)
from vim_adaptor.util import create_completed_response, create_error_response

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
        self.conn.register_async_endpoint(
            self.add_vim, "infrastructure.management.compute.add"
        )
        self.conn.register_async_endpoint(
            self.delete_vim, "infrastructure.management.compute.remove"
        )
        self.conn.register_async_endpoint(
            self.list_vims, "infrastructure.management.compute.list"
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

        if vim_type == "openStack":
            schema = OpenStackVimSchema()
        elif vim_type == "kubernetes":
            schema = KubernetesVimSchema()
        elif vim_type == "aws":
            schema = AwsVimSchema()

        vim, errors = schema.load(payload)
        if len(errors) > 0:
            return create_error_response(str(errors))

        vim.save()
        return create_completed_response({"uuid": str(vim.id)})

    def list_vims(self, message: Message):
        return [
            {
                "vim_uuid": str(vim.id),
                "vim_name": vim.name,
                "vim_country": vim.country,
                "vim_city": vim.city,
                "type": vim.type,
                "memory_total": 32000,
                "memory_used": 0,
                "core_total": 4,
                "core_used": 0,
            }
            for vim in BaseVim.objects
        ]

    def delete_vim(self, message: Message):
        payload = message.payload
        if "uuid" not in payload:
            return create_error_response(
                'The request message does not contain a "uuid" field.'
            )

        id = payload["uuid"]

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


def main():
    VimAdaptor()


if __name__ == "__main__":
    main()
