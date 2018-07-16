#!/usr/bin/env python3

############################################################################
# Copyright 2017 RIFT.IO Inc                                               #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License");          #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http://www.apache.org/licenses/LICENSE-2.0                           #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################


import argparse
import os
import sys
import random
import paramiko
import yaml
from glob import glob


def copy_file_ssh_sftp(server, remote_dir, remote_file, local_file):
    """Copy file to VM."""
    sshclient = paramiko.SSHClient()
    sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sshclient.load_system_host_keys(filename="/dev/null")
    sshclient.connect(server, username="fedora", password="fedora")
    sftpclient = sshclient.open_sftp()
    sftpclient.put(local_file, remote_dir + '/' + remote_file)
    sshclient.close()


def get_full_path(file_name, production_launchpad=True):
    """Return the full path for the init cfg file."""
    mpath = os.path.join(
        os.getenv('RIFT_INSTALL'), 'var', 'rift')
    if not production_launchpad:
        launchpad_folder = glob('{}/*mgmt-vm-lp-2'.format(mpath))[0]
    else:
        launchpad_folder = ''
    mpath = os.path.join(
        os.getenv('RIFT_INSTALL'), 'var', 'rift', launchpad_folder,
        'launchpad', 'packages', 'vnfd', 'default')
    vnfd_folder = random.choice(
        [x for x in os.listdir(mpath) if os.path.isdir(
            os.path.join(mpath, x))])
    full_path = glob(
        '{}/{}/cloud_init/{}'.format(mpath, vnfd_folder, file_name))[0]
    file_name = os.path.basename(os.path.normpath(full_path))
    return full_path, file_name


def exists_remote(host, path):
    """Test if a file exists at path on a host accessible with SSH."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username="fedora", password="fedora")
        sftp = ssh.open_sftp()
        try:
            sftp.stat(path)
        except Exception:
            raise Exception('Transfered file not found on the remote host')
        ssh.close()
    except paramiko.SSHException:
        print("Connection Error")


def primitive_test(yaml_cfg):
    """Transfer a cloud init file from the vnfd descriptor package.

    Verify that the file is transfered.
    """
    for index, vnfr in yaml_cfg['vnfr_data_map'].items():
        vnfd_ip = vnfr['mgmt_interface']['ip_address']
        file_name = '*_cloud_init.cfg'
        local_file, file_name = get_full_path(file_name)
        copy_file_ssh_sftp(vnfd_ip, '/tmp/', file_name, local_file)
        remote_file_path = os.path.join(
            '/'
            'tmp',
            file_name)
        exists_remote(vnfd_ip, remote_file_path)


def main(argv=sys.argv[1:]):
    """Main."""
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("yaml_cfg_file", type=argparse.FileType('r'))
        parser.add_argument(
            "-q", "--quiet", dest="verbose",
            action="store_false")
        args = parser.parse_args()

    except Exception as e:
        print("Exception in {}: {}".format(__file__, e))
        sys.exit(1)

    try:
        yaml_str = args.yaml_cfg_file.read()
        yaml_cfg = yaml.load(yaml_str)

        primitive_test(yaml_cfg)

    except Exception as e:
        print("Exception: {}".format(e))
        raise e

if __name__ == "__main__":
    main()
