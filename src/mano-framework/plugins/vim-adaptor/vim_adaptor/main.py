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
import time

from config2.config import config
from mongoengine import connect

from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin

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

    def run(self):
        """
        To be overwritten by subclass
        """
        # go into infinity loop (we could do anything here)
        while True:
            time.sleep(1)
            print("lol")

    def declare_subscriptions(self):
        super().declare_subscriptions()

    def on_lifecycle_start(self, message: Message):
        super().on_lifecycle_start(message)
        LOG.info("VIM Adaptor started.")


def main():
    VimAdaptor()


if __name__ == "__main__":
    main()
