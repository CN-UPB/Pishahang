
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

import gi
import shlex
import pytest
import os
import subprocess
import tempfile

from gi.repository import (
    ProjectNsdYang as NsdYang,
    NsrYang,
    RwNsrYang,
    RwVnfrYang,
    VnfrYang,
    VldYang,
    RwProjectVnfdYang as RwVnfdYang,
    RwLaunchpadYang,
    RwBaseYang
)

@pytest.fixture(scope='session', autouse=True)
def cloud_account_name(request):
    '''fixture which returns the name used to identify the cloud account'''
    return 'cloud-0'

@pytest.fixture(scope='session')
def launchpad_host(request, confd_host):
    return confd_host

@pytest.fixture(scope='session')
def vnfd_proxy(request, mgmt_session):
    return mgmt_session.proxy(RwVnfdYang)

@pytest.fixture(scope='session')
def vnfr_proxy(request, mgmt_session):
    return mgmt_session.proxy(VnfrYang)

@pytest.fixture(scope='session')
def rwvnfr_proxy(request, mgmt_session):
    return mgmt_session.proxy(RwVnfrYang)

@pytest.fixture(scope='session')
def vld_proxy(request, mgmt_session):
    return mgmt_session.proxy(VldYang)

@pytest.fixture(scope='session')
def nsd_proxy(request, mgmt_session):
    return mgmt_session.proxy(NsdYang)

@pytest.fixture(scope='session')
def nsr_proxy(request, mgmt_session):
    return mgmt_session.proxy(NsrYang)

@pytest.fixture(scope='session')
def rwnsr_proxy(request, mgmt_session):
    return mgmt_session.proxy(RwNsrYang)

@pytest.fixture(scope='session')
def base_proxy(request, mgmt_session):
    return mgmt_session.proxy(RwBaseYang)

@pytest.fixture(scope='session')
def base_proxy(request, mgmt_session):
    return mgmt_session.proxy(RwBaseYang)

@pytest.fixture(scope='session')
def mvv_descr_dir(request):
    """root-directory of descriptors files used for Multi-VM VNF"""
    return os.path.join(
        os.environ["RIFT_INSTALL"],
        "demos/tests/multivm_vnf"
        )

@pytest.fixture(scope='session')
def package_dir(request):
    return tempfile.mkdtemp(prefix="mvv_")

@pytest.fixture(scope='session')
def trafgen_vnfd_package_file(request, package_gen_script, mvv_descr_dir, package_dir):
    pkg_cmd = "{pkg_scr} --descriptor-type='vnfd' --format='xml' --infile='{infile}' --outdir='{outdir}'".format(
            pkg_scr=package_gen_script,
            outdir=package_dir,
            infile=os.path.join(mvv_descr_dir, 'vnfd/xml/multivm_trafgen_vnfd.xml'))
    pkg_file = os.path.join(package_dir, 'multivm_trafgen_vnfd.tar.gz')
    command = shlex.split(pkg_cmd)
    print("Running the command arguments: %s" % command)
    command = [package_gen_script,
               "--descriptor-type", "vnfd",
               "--format", "xml",
               "--infile", "%s" % os.path.join(mvv_descr_dir, 'vnfd/xml/multivm_trafgen_vnfd.xml'),
               "--outdir", "%s" % package_dir]
    print("Running new command arguments: %s" % command)
    subprocess.check_call(command)
    return pkg_file

@pytest.fixture(scope='session')
def trafsink_vnfd_package_file(request, package_gen_script, mvv_descr_dir, package_dir):
    pkg_cmd = "{pkg_scr} --descriptor-type='vnfd' --format='xml' --infile='{infile}' --outdir='{outdir}'".format(
            pkg_scr=package_gen_script,
            outdir=package_dir,
            infile=os.path.join(mvv_descr_dir, 'vnfd/xml/multivm_trafsink_vnfd.xml'))
    pkg_file = os.path.join(package_dir, 'multivm_trafsink_vnfd.tar.gz')
    command = shlex.split(pkg_cmd)
    print("Running the command arguments: %s" % command)
    command = [package_gen_script,
               "--descriptor-type", "vnfd",
               "--format", "xml",
               "--infile", "%s" % os.path.join(mvv_descr_dir, 'vnfd/xml/multivm_trafsink_vnfd.xml'),
               "--outdir", "%s" % package_dir]
    print("Running new command arguments: %s" % command)
    subprocess.check_call(command)
    return pkg_file

@pytest.fixture(scope='session')
def slb_vnfd_package_file(request, package_gen_script, mvv_descr_dir, package_dir):
    pkg_cmd = "{pkg_scr} --outdir {outdir} --infile {infile} --descriptor-type vnfd --format xml".format(
            pkg_scr=package_gen_script,
            outdir=package_dir,
            infile=os.path.join(mvv_descr_dir, 'vnfd/xml/multivm_slb_vnfd.xml'),
            )
    pkg_file = os.path.join(package_dir, 'multivm_slb_vnfd.tar.gz')
    subprocess.check_call(shlex.split(pkg_cmd))
    return pkg_file
