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
import json
from mongoengine import connect
from config2.config import config

from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin
from vim_adaptor.models.vims import Vim, Aws, Kubernetes, OpenStack
from vim_adaptor.util.mongoengine_custom_json import to_custom_dict
from vim_adaptor.util.mongoengine_custom_json import to_custom_json

logging.basicConfig(level=logging.INFO)
logging.getLogger("manobase:plugin").setLevel(logging.INFO)
logging.getLogger("amqpstorm.channel").setLevel(logging.ERROR)

LOG = logging.getLogger("plugin:vim-adaptor")
LOG.setLevel(logging.DEBUG)


class VimAdaptor(ManoBasePlugin):
    """
    Vim Adaptor main class. Instantiate this class to run the Vim Adaptor.
    """

    def __init__(self, *args, **kwargs):
        # Connect to MongoDB
        LOG.debug("Connecting to MongoDB at %s", config.mongo)
        connect(host=config.mongo)
        LOG.info("Connected to MongoDB")

        kwargs.update({"version": "0.1.0", "start_running": False})
        super().__init__(*args, **kwargs)

    def declare_subscriptions(self):
        super().declare_subscriptions()
        self.manoconn.register_async_endpoint(
            self.add_vim, "infrastructure.management.compute.add"
        )
        self.manoconn.register_async_endpoint(
            self.delete_vim, "infrastructure.management.compute.remove"
        )
        self.manoconn.register_async_endpoint(
            self.get_vim, "infrastructure.management.compute.list"
        )

    def on_lifecycle_start(self, message: Message):
        super().on_lifecycle_start(message)
        LOG.info("VIM Adaptor started.")

    def add_vim(self, message: Message):
        vim_type = message.payload["type"]
        if vim_type == "aws":
            vim = Aws(
                vimCity=message.payload["city"],
                vimName=message.payload["name"],
                country=message.payload["country"],
                accessKey=message.payload["accessKey"],
                secretKey=message.payload["secretKey"],
                type=message.payload["type"],
            )
        elif vim_type == "kubernetes":
            vim = Kubernetes(
                vimName=message.payload["name"],
                country=message.payload["country"],
                vimCity=message.payload["city"],
                type=message.payload["type"],
                vimAddress=message.payload["vimAddress"],
                serviceToken=message.payload["serviceToken"],
                ccc=message.payload["ccc"],
            )
        elif vim_type == "openStack":
            vim = OpenStack(
                vimName=message.payload["name"],
                country=message.payload["country"],
                vimCity=message.payload["vimCity"],
                vimAddress=message.payload["vimAddress"],
                tenantId=message.payload["tenantId"],
                tenantExternalNetworkId=message.payload["tenantExternalNetworkId"],
                tenantExternalRouterId=message.payload["tenantExternalRouterId"],
                username=message.payload["username"],
                password=message.payload["password"],
                type=message.payload["type"],
            )
        LOG.debug("Add vim: %s", message.payload)
        vim.save()

    def get_vim(self, message: Message):
        vims = Vim.objects
        LOG.debug("List of vim: %s", message.payload)
        return vims

    def delete_vim(self, message: Message):
        id = Message.payload["uuid"]
        vim = Vim.objects(id=id).get()
        LOG.debug("Vim Delete: %s", message.payload)
        vim.delete()


def main():
    # Connect to MongoDB
    LOG.debug("Connecting to MongoDB at %s", config.mongo)
    connect(host=config.mongo)
    LOG.info("Connected to MongoDB")

    VimAdaptor()


if __name__ == "__main__":
    main()
