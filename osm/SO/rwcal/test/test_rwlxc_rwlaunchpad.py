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


import logging
import os

import rift.rwcal.cloudsim.lxc as lxc
import rift.rwcal.cloudsim.lvm as lvm


logger = logging.getLogger('rwcal-test')


def main():
    template = os.path.realpath("../rift/cal/lxc-fedora-rift.lxctemplate")
    tarfile = "/net/strange/localdisk/jdowner/lxc.tar.gz"
    volume = 'rift-test'

    lvm.create(volume, '/lvm/rift-test.img')

    master = lxc.create_container('test-master', template, volume, tarfile)

    snapshots = []
    for index in range(5):
        snapshots.append(master.snapshot('test-snap-{}'.format(index + 1)))

    for snapshot in snapshots:
        snapshot.destroy()

    master.destroy()

    lvm.destroy(volume)



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
