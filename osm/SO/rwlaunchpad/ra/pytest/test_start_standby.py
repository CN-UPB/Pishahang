"""
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

@file  test_start_standby.py
@brief This test starts the launchpad on a remote VM
"""
import argparse
import sys
import time
import os
import glob
import subprocess
import shlex
import multiprocessing

import rift.auto.session
import rift.vcs.vcs

def get_manifest_file():
    artifacts_path = os.environ["RIFT_ARTIFACTS"]
    manifest_files = glob.glob(artifacts_path + "/manifest*xml")
    manifest_files.sort(key=lambda x: os.stat(x).st_mtime)
    return manifest_files[0]

def copy_manifest_to_remote(remote_ip, manifest_file):
    print ("Copying manifest file {} to remote".format(manifest_file))
    cmd = "scp {0} {1}:/tmp/manifest.xml".format(manifest_file, remote_ip)
    print ("Running command: {}".format(cmd))
    subprocess.check_call(cmd, shell=True)
    

def test_start_lp_remote(remote_ip):
    rift_root = os.environ.get('HOME_RIFT', os.environ.get('RIFT_ROOT'))
    rift_install = os.environ.get('RIFT_INSTALL')

    copy_manifest_to_remote(remote_ip, get_manifest_file())

    cmd_template = ("ssh_root {remote_ip} -q -o BatchMode=yes -o "
    " UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -- "
    " \"rm -rf /tmp/corosync; cd {rift_install}; {rift_root}/rift-shell -- {rift_install}/usr/bin/rwmain -m /tmp/manifest.xml\"").format(
      remote_ip=remote_ip,
      rift_root=rift_root,
      rift_install=rift_install)

    def start_lp(cmd):
        print ("Running cmd: {}".format(cmd))
        subprocess.call(shlex.split(cmd))

    print ("Starting launchpad on remote VM: {}".format(cmd_template))
    p = multiprocessing.Process(target=start_lp, args=(cmd_template,))
    p.daemon = True
    p.start()
    print ("Standby system started")
    time.sleep(60)
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start standby LP')
    parser.add_argument("--remote-ip", action="store", dest="remote_ip")

    args = parser.parse_args()

    test_start_lp_remote(args.remote_ip)
