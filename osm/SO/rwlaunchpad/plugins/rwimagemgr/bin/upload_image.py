#!/usr/bin/env python3

# 
#   Copyright 2016 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#


import argparse
import asyncio
import logging
import sys

from rift.tasklets.rwimagemgr import tasklet, glance_client
from rift.mano.cloud import accounts

import gi
gi.require_version('RwCloudYang', '1.0')
gi.require_version('RwLog', '1.0')
from gi.repository import (
        RwCloudYang,
        RwLog,
        )

openstack_info = {
        'username': 'pluto',
        'password': 'mypasswd',
        'project_name': 'demo',
        'auth_url': 'http://10.66.4.18:5000/v3',
        'mgmt_network': 'private'
        }


def create_account(log):
    account_msg = RwCloudYang.YangData_RwProject_Project_CloudAccounts_CloudAccountList.from_dict(dict(
        name="openstack",
        account_type="openstack",
        openstack=dict(
            key=openstack_info["username"],
            secret=openstack_info["password"],
            tenant=openstack_info["project_name"],
            auth_url=openstack_info["auth_url"]
            )
        )
    )

    account = accounts.CloudAccount(
            log,
            RwLog.Ctx.new(__file__),
            account_msg
            )

    return account


def parse_args(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-name", required=True)
    parser.add_argument("--image-checksum", required=True)

    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("upload_image.py")
    loop = asyncio.get_event_loop()
    cloud_account = create_account(log)
    client = glance_client.OpenstackGlanceClient.from_token(
            log, "127.0.0.1", 9292, "test"
            )
    task_creator = tasklet.GlanceClientUploadTaskCreator(
            log, loop, {"openstack": cloud_account}, client,
            )

    tasks = loop.run_until_complete(
            task_creator.create_tasks(
                ["openstack"],
                args.image_name,
                args.image_checksum
                )
            )

    log.debug("Created tasks: %s", tasks)

    log.debug("uploading images")
    loop.run_until_complete(asyncio.wait([t.start() for t in tasks], loop=loop))


if __name__ == "__main__":
    main()
