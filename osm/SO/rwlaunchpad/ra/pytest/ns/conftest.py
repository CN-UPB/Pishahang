
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

import functools
import hashlib
import pytest
import os
import tempfile
import shutil
import subprocess
import random

import gi
import rift.auto.descriptor
import rift.auto.session
import rift.mano.examples.ping_pong_nsd as ping_pong_example
import rift.vcs.vcs

class PackageError(Exception):
    pass

@pytest.fixture(scope='session', autouse=True)
def multidisk_testdata(request, descriptor_images, path_ping_image, path_pong_image):
    """fixture which returns test data related to multidisk test"""

    if not request.config.option.multidisk:
        return None

    iso_img, qcow2_img = [os.path.basename(image) for image in descriptor_images]
    
    ping_ = {'vda': ['disk', 'virtio', 5, os.path.basename(path_ping_image), 0],
             'sda': ['cdrom', 'scsi', 5, iso_img, 1],
             'hda': ['disk', 'ide', 5, None, None],
             }

    pong_ = {'vda': ['disk', 'virtio', 5, os.path.basename(path_pong_image), 0],
             'hda': ['cdrom', 'ide', 5, iso_img, 1],
             'hdb': ['disk', 'ide', 5, qcow2_img, 2],
             }
    return ping_, pong_

@pytest.fixture(scope='session')
def port_sequencing_intf_positions():
    """fixture which returns a list of ordered positions for pong interfaces related to port sequencing test"""
    return random.sample(range(1, 2**32-1), 3)

@pytest.fixture(scope='session')
def ping_pong_install_dir():
    '''Fixture containing the location of ping_pong installation
    '''
    install_dir = os.path.join(
        os.environ["RIFT_ROOT"],
        "images"
        )
    return install_dir

@pytest.fixture(scope='session')
def ping_vnfd_package_file(ping_pong_install_dir):
    '''Fixture containing the location of the ping vnfd package

    Arguments:
        ping_pong_install_dir - location of ping_pong installation
    '''
    ping_pkg_file = os.path.join(
            ping_pong_install_dir,
            "ping_vnfd_with_image.tar.gz",
            )
    if not os.path.exists(ping_pkg_file):
        raise_package_error()

    return ping_pkg_file


@pytest.fixture(scope='session')
def pong_vnfd_package_file(ping_pong_install_dir):
    '''Fixture containing the location of the pong vnfd package

    Arguments:
        ping_pong_install_dir - location of ping_pong installation
    '''
    pong_pkg_file = os.path.join(
            ping_pong_install_dir,
            "pong_vnfd_with_image.tar.gz",
            )
    if not os.path.exists(pong_pkg_file):
        raise_package_error()

    return pong_pkg_file


@pytest.fixture(scope='session')
def ping_pong_nsd_package_file(ping_pong_install_dir):
    '''Fixture containing the location of the ping_pong_nsd package

    Arguments:
        ping_pong_install_dir - location of ping_pong installation
    '''
    ping_pong_pkg_file = os.path.join(
            ping_pong_install_dir,
            "ping_pong_nsd.tar.gz",
            )
    if not os.path.exists(ping_pong_pkg_file):
        raise_package_error()

    return ping_pong_pkg_file

@pytest.fixture(scope='session')
def image_dirs():
    ''' Fixture containing a list of directories where images can be found
    '''
    rift_build = os.environ['RIFT_BUILD']
    rift_root = os.environ['RIFT_ROOT']
    image_dirs = [
        os.path.join(
            rift_build,
            "modules/core/mano/src/core_mano-build/examples/",
            "ping_pong_ns/ping_vnfd_with_image/images"
        ),
        os.path.join(
            rift_root,
            "images"
        )
    ]
    return image_dirs

@pytest.fixture(scope='session')
def random_image_name(image_dirs):
    """Fixture which returns a random image name"""
    return 'image_systemtest_{}.qcow2'.format(random.randint(100, 9999))

@pytest.fixture(scope='session')
def image_paths(image_dirs):
    ''' Fixture containing a mapping of image names to their path images

    Arguments:
        image_dirs - a list of directories where images are located
    '''
    image_paths = {}
    for image_dir in image_dirs:
        if os.path.exists(image_dir):
            names = os.listdir(image_dir)
            image_paths.update({name:os.path.join(image_dir, name) for name in names})
    return image_paths

@pytest.fixture(scope='session')
def path_ping_image(image_paths):
    ''' Fixture containing the location of the ping image

    Arguments:
        image_paths - mapping of images to their paths
    '''
    return image_paths["Fedora-x86_64-20-20131211.1-sda-ping.qcow2"]

@pytest.fixture(scope='session')
def path_pong_image(image_paths):
    ''' Fixture containing the location of the pong image

    Arguments:
        image_paths - mapping of images to their paths
    '''
    return image_paths["Fedora-x86_64-20-20131211.1-sda-pong.qcow2"]

@pytest.fixture(scope='session')
def rsyslog_userdata(rsyslog_host, rsyslog_port):
    ''' Fixture providing rsyslog user data
    Arguments:
        rsyslog_host - host of the rsyslog process
        rsyslog_port - port of the rsyslog process
    '''
    if rsyslog_host and rsyslog_port:
        return '''
rsyslog:
  - "$ActionForwardDefaultTemplate RSYSLOG_ForwardFormat"
  - "*.* @{host}:{port}"
        '''.format(
            host=rsyslog_host,
            port=rsyslog_port,
        )

    return None

@pytest.fixture(scope='session')
def descriptors_pingpong_vnf_input_params():
    return ping_pong_example.generate_ping_pong_descriptors(
        pingcount=1,
        nsd_name='pp_input_nsd',
        vnfd_input_params=True,
    )

@pytest.fixture(scope='session')
def packages_pingpong_vnf_input_params(descriptors_pingpong_vnf_input_params):
    return rift.auto.descriptor.generate_descriptor_packages(descriptors_pingpong_vnf_input_params)

@pytest.fixture(scope='session')
def ping_script_userdata():
    userdata = '''#cloud-config
password: fedora
chpasswd: { expire: False }
ssh_pwauth: True
runcmd:
  - [ systemctl, daemon-reload ]
  - [ systemctl, enable, {{ CI-script-init-data }}.service ]
  - [ systemctl, start, --no-block, {{ CI-script-init-data }}.service ]
  - [ ifup, eth1 ]
'''
    return userdata

@pytest.fixture(scope='session')
def pong_script_userdata():
    userdata = '''#!/bin/bash
sed 's/^.*PasswordAuthentication.*$/PasswordAuthentication yes/' < /etc/ssh/sshd_config > /etc/ssh/sshd_config
systemctl daemon-reload
systemctl enable {{ CI-script-init-data }}.service
systemctl start --no-block {{ CI-script-init-data }}.service
ifup eth1
'''
    return userdata

@pytest.fixture(scope='session')
def descriptors_pingpong_script_input_params(ping_script_userdata, pong_script_userdata):
    return ping_pong_example.generate_ping_pong_descriptors(
            pingcount=1,
            nsd_name='pp_script_nsd',
            script_input_params=True,
            ping_userdata=ping_script_userdata,
            pong_userdata=pong_script_userdata,
    )

@pytest.fixture(scope='session')
def packages_pingpong_script_input_params(descriptors_pingpong_script_input_params):
    return rift.auto.descriptor.generate_descriptor_packages(descriptors_pingpong_script_input_params)

class PingPongFactory:
    def __init__(self, path_ping_image, path_pong_image, static_ip, vnf_dependencies, rsyslog_userdata, port_security, metadata_vdud, multidisk, ipv6, port_sequencing, service_primitive):

        self.path_ping_image = path_ping_image
        self.path_pong_image = path_pong_image
        self.rsyslog_userdata = rsyslog_userdata
        self.static_ip = static_ip
        self.service_primitive = service_primitive
        self.use_vca_conf = vnf_dependencies
        self.port_security = port_security
        self.port_sequencing = port_sequencing
        self.metadata_vdud = metadata_vdud
        self.multidisk = multidisk
        self.ipv6 = ipv6
        if not port_security:
            self.port_security = None   # Not to disable port security if its not specific to --port-security feature.

    def generate_descriptors(self):
        '''Return a new set of ping and pong descriptors
        '''
        def md5sum(path):
            with open(path, mode='rb') as fd:
                md5 = hashlib.md5()
                for buf in iter(functools.partial(fd.read, 4096), b''):
                    md5.update(buf)
            return md5.hexdigest()

        ping_md5sum = md5sum(self.path_ping_image)
        pong_md5sum = md5sum(self.path_pong_image)

        descriptors = ping_pong_example.generate_ping_pong_descriptors(
                pingcount=1,
                ping_md5sum=ping_md5sum,
                pong_md5sum=pong_md5sum,
                ex_ping_userdata=self.rsyslog_userdata,
                ex_pong_userdata=self.rsyslog_userdata,
                use_static_ip=self.static_ip,
                port_security=self.port_security,
                explicit_port_seq=self.port_sequencing,
                metadata_vdud=self.metadata_vdud,
                use_vca_conf=self.use_vca_conf,
                multidisk=self.multidisk,
                use_ipv6=self.ipv6,
                primitive_test=self.service_primitive,
        )

        return descriptors

@pytest.fixture(scope='session')
def ping_pong_factory(path_ping_image, path_pong_image, static_ip, vnf_dependencies, rsyslog_userdata, port_security, metadata_vdud, multidisk_testdata, ipv6, port_sequencing, service_primitive):
    '''Fixture returns a factory capable of generating ping and pong descriptors
    '''
    return PingPongFactory(path_ping_image, path_pong_image, static_ip, vnf_dependencies, rsyslog_userdata, port_security, metadata_vdud, multidisk_testdata, ipv6, port_sequencing, service_primitive)

@pytest.fixture(scope='session')
def ping_pong_records(ping_pong_factory):
    '''Fixture returns the default set of ping_pong descriptors
    '''
    return ping_pong_factory.generate_descriptors()


@pytest.fixture(scope='session')
def descriptors(request, ping_pong_records, random_image_name):
    def pingpong_descriptors(with_images=True):
        """Generated the VNFDs & NSD files for pingpong NS.

        Returns:
            Tuple: file path for ping vnfd, pong vnfd and ping_pong_nsd
        """
        ping_vnfd, pong_vnfd, ping_pong_nsd = ping_pong_records

        tmpdir = tempfile.mkdtemp()
        rift_build = os.environ['RIFT_BUILD']
        MANO_DIR = os.path.join(
                rift_build,
                "modules/core/mano/src/core_mano-build/examples/ping_pong_ns")
        ping_img = os.path.join(MANO_DIR, "ping_vnfd_with_image/images/Fedora-x86_64-20-20131211.1-sda-ping.qcow2")
        pong_img = os.path.join(MANO_DIR, "pong_vnfd_with_image/images/Fedora-x86_64-20-20131211.1-sda-pong.qcow2")

        """ grab cached copies of these files if not found. They may not exist 
            because our git submodule dependency mgmt
            will not populate these because they live in .build, not .install
        """
        if not os.path.exists(ping_img):
            ping_img = os.path.join(
                        os.environ['RIFT_ROOT'], 
                        'images/Fedora-x86_64-20-20131211.1-sda-ping.qcow2')
            pong_img = os.path.join(
                        os.environ['RIFT_ROOT'], 
                        'images/Fedora-x86_64-20-20131211.1-sda-pong.qcow2')

        for descriptor in [ping_vnfd, pong_vnfd, ping_pong_nsd]:
            descriptor.write_to_file(output_format='yaml', outdir=tmpdir)
        ping_img_path = os.path.join(tmpdir, "{}/images/".format(ping_vnfd.name))
        pong_img_path = os.path.join(tmpdir, "{}/images/".format(pong_vnfd.name))

        if with_images:
            os.makedirs(ping_img_path)
            os.makedirs(pong_img_path)
            shutil.copy(ping_img, ping_img_path)
            shutil.copy(pong_img, pong_img_path)

        if request.config.option.upload_images_multiple_accounts:
            with open(os.path.join(ping_img_path, random_image_name), 'wb') as image_bin_file:
                image_bin_file.seek(1024*1024*512)  # image file of size 512 MB
                image_bin_file.write(b'0')

        for dir_name in [ping_vnfd.name, pong_vnfd.name, ping_pong_nsd.name]:
            subprocess.call([
                    "{rift_install}/usr/rift/toolchain/cmake/bin/generate_descriptor_pkg.sh".format(rift_install=os.environ['RIFT_INSTALL']),
                    tmpdir,
                    dir_name])

        return (os.path.join(tmpdir, "{}.tar.gz".format(ping_vnfd.name)),
                os.path.join(tmpdir, "{}.tar.gz".format(pong_vnfd.name)),
                os.path.join(tmpdir, "{}.tar.gz".format(ping_pong_nsd.name)))

    def haproxy_descriptors():
        """HAProxy descriptors."""
        files = [
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/http_client/http_client_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/httpd/httpd_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/haproxy/haproxy_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/waf/waf_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/haproxy_waf_httpd_nsd/haproxy_waf_httpd_nsd.tar.gz")
            ]

        return files

    def l2portchain_descriptors():
        """L2  port chaining packages"""
        files = [
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/vnffg_demo_nsd/vnffg_l2portchain_dpi_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/vnffg_demo_nsd/vnffg_l2portchain_firewall_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/vnffg_demo_nsd/vnffg_l2portchain_nat_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/vnffg_demo_nsd/vnffg_l2portchain_pgw_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/vnffg_demo_nsd/vnffg_l2portchain_router_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/vnffg_demo_nsd/vnffg_l2portchain_sff_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/vnffg_demo_nsd/vnffg_l2portchain_demo_nsd.tar.gz")
            ]

        return files

    def metadata_vdud_cfgfile_descriptors():
        """Metadata-vdud feature related packages"""
        files = [
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/cfgfile/cirros_cfgfile_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/cfgfile/fedora_cfgfile_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/cfgfile/ubuntu_cfgfile_vnfd.tar.gz"),
            os.path.join(os.getenv('RIFT_BUILD'), "modules/ext/vnfs/src/ext_vnfs-build/cfgfile/cfgfile_nsd.tar.gz")
            ]

        return files
        
    if request.config.option.vnf_onboard_delete:
        return haproxy_descriptors() + l2portchain_descriptors() + list(pingpong_descriptors())
    if request.config.option.multiple_ns_instantiate:
        return haproxy_descriptors() + metadata_vdud_cfgfile_descriptors() + list(pingpong_descriptors())
    if request.config.option.l2_port_chaining:
        return l2portchain_descriptors()
    if request.config.option.metadata_vdud_cfgfile:
        return metadata_vdud_cfgfile_descriptors()
    if request.config.option.network_service == "pingpong":
        return pingpong_descriptors()
    elif request.config.option.ha_multiple_failovers:
        return {'pingpong': pingpong_descriptors(), 'haproxy': haproxy_descriptors(), 'vdud_cfgfile': metadata_vdud_cfgfile_descriptors()}
    elif request.config.option.network_service == "pingpong_noimg":
        return pingpong_descriptors(with_images=False)
    elif request.config.option.network_service == "haproxy":
        return haproxy_descriptors()


@pytest.fixture(scope='session')
def descriptor_images(request):
    def haproxy_images():
        """HAProxy images."""
        images = [
            os.path.join(os.getenv('RIFT_ROOT'), "images/haproxy-v03.qcow2"),
            os.path.join(os.getenv('RIFT_ROOT'), "images/web-app-firewall-v02.qcow2"),
            os.path.join(os.getenv('RIFT_ROOT'), "images/web-server-v02.qcow2")
            ]

        return images

    def l2portchain_images():
        """HAProxy images."""
        images = [os.path.join(os.getenv('RIFT_ROOT'), "images/ubuntu_trusty_1404.qcow2")]
        return images

    def multidisk_images():
        images = [
            os.path.join(os.getenv('RIFT_ROOT'), 'images/ubuntu-16.04-mini-64.iso'),
            os.path.join(os.getenv('RIFT_ROOT'), "images/ubuntu_trusty_1404.qcow2"),
            ]
        return images

    def metadata_vdud_cfgfile_images():
        """Metadata-vdud feature related images."""
        images = [
            os.path.join(os.getenv('RIFT_ROOT'), "images/cirros-0.3.4-x86_64-disk.img"),
            os.path.join(os.getenv('RIFT_ROOT'), "images/Fedora-x86_64-20-20131211.1-sda.qcow2"),
            os.path.join(os.getenv('RIFT_ROOT'), "images/UbuntuXenial")
            ]

        return images

    if request.config.option.l2_port_chaining:
        return l2portchain_images()
    if request.config.option.multidisk:
        return multidisk_images()
    if request.config.option.metadata_vdud_cfgfile:
        return metadata_vdud_cfgfile_images()
    if request.config.option.network_service == "haproxy":
        return haproxy_images()
    if request.config.option.multiple_ns_instantiate:
        return haproxy_images() + metadata_vdud_cfgfile_images()

    return []
