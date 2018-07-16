#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Copyright 2016 RIFT.io Inc


import argparse
import logging
import os
import socket
import stat
import sys
import tempfile

from Crypto.PublicKey import RSA


class ManoSshKey(object):
    '''
    Generate a SSH key pair and store them in a file
    '''

    def __init__(self, log, size=2048):
        self._log = log
        self._size = size

        self._key = None
        self._key_pem = None
        self._pub_ssh = None
        self._key_file = None
        self._pub_file = None

    @property
    def log(self):
        return self._log

    @property
    def size(self):
        return self._size

    @property
    def private_key(self):
        if self._key is None:
            self._gen_keys()
        return self._key_pem

    @property
    def public_key(self):
        if self._key is None:
            self._gen_keys()
        return self._pub_ssh

    @property
    def private_key_file(self):
        return self._key_file

    @property
    def public_key_file(self):
        return self._pub_file

    def _gen_keys(self):
        if self._key:
            return

        self.log.info("Generating key of size: {}".format(self.size))

        self._key = RSA.generate(self.size, os.urandom)
        self._key_pem = self._key.exportKey('PEM').decode('utf-8')
        self.log.debug("Private key PEM: {}".format(self._key_pem))

        # Public key export as 'OpenSSH' has a bug
        # (https://github.com/dlitz/pycrypto/issues/99)

        username = None
        try:
            username = os.getlogin()
            hostname = socket.getfqdn()
        except OSError:
            pass

        pub = self._key.publickey().exportKey('OpenSSH').decode('utf-8')
        if username:
            self._pub_ssh = '{} {}@{}'.format(pub, username, hostname)
        else:
            self._pub_ssh = pub
        self.log.debug("Public key SSH: {}".format(self._pub_ssh))

    def write_to_disk(self,
                      name="id_rsa",
                      directory="."):
        if self._key is None:
            self._gen_keys()

        path = os.path.abspath(directory)
        self._pub_file = "{}/{}.pub".format(path, name)
        self._key_file = "{}/{}.key".format(path, name)

        with open(self._key_file, 'w') as content_file:
            content_file.write(self.private_key)
            os.chmod(self._key_file, stat.S_IREAD|stat.S_IWRITE)

        with open(self._pub_file, 'w') as content_file:
            content_file.write(self.public_key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate SSH key pair')
    parser.add_argument("-s", "--size", type=int, default=2048, help="Key size")
    parser.add_argument("-d", "--directory", help="Directory to store the keys")
    parser.add_argument("-n", "--name", help="Name for the key file")
    parser.add_argument("--debug", help="Enable debug logging",
                        action="store_true")
    args = parser.parse_args()

    fmt = logging.Formatter(
        '%(asctime)-23s %(levelname)-5s  (%(name)s@%(process)d:' \
        '%(filename)s:%(lineno)d) - %(message)s')
    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_handler.setFormatter(fmt)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('rw-mano-ssh-keys')
    log.addHandler(stderr_handler)

    log.info("Args passed: {}".format(args))
    if args.directory:
        path = args.directory
    else:
        path = tempfile.mkdtemp()

    kp = ManoSshKey(log, size=args.size)
    kp.write_to_disk(directory=path)
    log.info("Private Key: {}".format(kp.private_key))
    log.info("Public key: {}".format(kp.public_key))
    log.info("Key file: {}, Public file: {}".format(kp.private_key_file,
                                                    kp.public_key_file))
