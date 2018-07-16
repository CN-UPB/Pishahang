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
import collections
import logging
import math
import os
import sys
import tempfile
import yaml
import ast
import json

import gi
gi.require_version('RwYang', '1.0')
gi.require_version('RwProjectVnfdYang', '1.0')
gi.require_version('RwProjectNsdYang', '1.0')
gi.require_version('NsdYang', '1.0')
gi.require_version('VnfdYang', '1.0')

from gi.repository import (
    RwYang,
    RwProjectVnfdYang as RwVnfdYang,
    RwProjectNsdYang as RwNsdYang,
    NsdYang as NsdYang,
    VnfdYang as VnfdYang
    )

import rift.package.store
import rift.package.cloud_init

logger = logging.getLogger("rift2openmano.py")


class VNFNotFoundError(Exception):
    pass


class RiftNSD(object):
    model = RwYang.Model.create_libyang()
    model.load_module('nsd')
    
    def __init__(self, descriptor):
        self._nsd = descriptor

    def __str__(self):
        return str(self._nsd)

    @property
    def name(self):
        return self._nsd.name

    @property
    def id(self):
        return self._nsd.id

    @property
    def vnfd_ids(self):
        return [c.vnfd_id_ref for c in self._nsd.constituent_vnfd]

    @property
    def constituent_vnfds(self):
        return self._nsd.constituent_vnfd

    @property
    def scaling_group_descriptor(self):
        return self._nsd.scaling_group_descriptor

    @property
    def vlds(self):
        return self._nsd.vld

    @property
    def cps(self):
        return self._nsd.connection_point

    @property
    def description(self):
        return self._nsd.description

    @classmethod
    def from_xml_file_hdl(cls, hdl):
        hdl.seek(0)
        descriptor = NsdYang.YangData_Nsd_NsdCatalog_Nsd()
        descriptor.from_xml_v2(RiftNSD.model, hdl.read())
        return cls(descriptor)

    @classmethod
    def from_yaml_file_hdl(cls, hdl):
        hdl.seek(0)
        descriptor = NsdYang.YangData_Nsd_NsdCatalog_Nsd()
        descriptor.from_yaml(RiftNSD.model, hdl.read())
        return cls(descriptor)

    def from_dict(self):
        descriptor = NsdYang.YangData_Nsd_NsdCatalog_Nsd.from_dict(self._nsd.as_dict(), ignore_missing_keys=True).to_json_without_namespace(RiftNSD.model)
        return descriptor


class RiftVNFD(object):
    model = RwYang.Model.create_libyang()
    model.load_module('vnfd')
    
    def __init__(self, descriptor):
        self._vnfd = descriptor

    def __str__(self):
        return str(self._vnfd)

    @property
    def id(self):
        return self._vnfd.id

    @property
    def name(self):
        return self._vnfd.name

    @property
    def description(self):
        return self._vnfd.description

    @property
    def cps(self):
        return self._vnfd.connection_point

    @property
    def vdus(self):
        return self._vnfd.vdu

    @property
    def internal_vlds(self):
        return self._vnfd.internal_vld

    @classmethod
    def from_xml_file_hdl(cls, hdl):
        hdl.seek(0)
        descriptor = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd()
        descriptor.from_xml_v2(RiftVNFD.model, hdl.read())
        return cls(descriptor)

    @classmethod
    def from_yaml_file_hdl(cls, hdl):
        hdl.seek(0)
        descriptor = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd()
        descriptor.from_yaml(RiftVNFD.model, hdl.read())
        return cls(descriptor)

    def from_dict(self):
        descriptor = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd.from_dict(self._vnfd.as_dict(), ignore_missing_keys=True).to_json_without_namespace(RiftVNFD.model)
        return descriptor


def is_writable_directory(dir_path):
    """ Returns True if dir_path is writable, False otherwise

    Arguments:
        dir_path - A directory path
    """
    if not os.path.exists(dir_path):
        raise ValueError("Directory does not exist: %s", dir_path)

    try:
        testfile = tempfile.TemporaryFile(dir=dir_path)
        testfile.close()
    except OSError:
        return False

    return True


def create_vnfd_from_files(vnfd_file_hdls):
    """ Create a list of RiftVNFD instances from xml/yaml file handles

    Arguments:
        vnfd_file_hdls - Rift VNFD XML/YAML file handles

    Returns:
        A list of RiftVNFD instances
    """
    vnfd_dict = {}
    for vnfd_file_hdl in vnfd_file_hdls:
        if vnfd_file_hdl.name.endswith("yaml") or vnfd_file_hdl.name.endswith("yaml"):
            vnfd = RiftVNFD.from_yaml_file_hdl(vnfd_file_hdl)
        else:
            vnfd = RiftVNFD.from_xml_file_hdl(vnfd_file_hdl)
        vnfd_dict[vnfd.id] = vnfd

    return vnfd_dict


def create_nsd_from_file(nsd_file_hdl):
    """ Create a list of RiftNSD instances from yaml/xml file handles

    Arguments:
        nsd_file_hdls - Rift NSD XML/yaml file handles

    Returns:
        A list of RiftNSD instances
    """
    if nsd_file_hdl.name.endswith("yaml") or nsd_file_hdl.name.endswith("yaml"):
        nsd = RiftNSD.from_yaml_file_hdl(nsd_file_hdl)
    else:
        nsd = RiftNSD.from_xml_file_hdl(nsd_file_hdl)
    return nsd


def ddict():
    return collections.defaultdict(dict)

def convert_vnfd_name(vnfd_name, member_idx):
    return vnfd_name + "__" + str(member_idx)


def rift2openmano_nsd(rift_nsd, rift_vnfds, openmano_vnfd_ids, http_api, rift_vnfd_id=None):
    try:
        if rift_vnfd_id is None:
            for vnfd_id in rift_nsd.vnfd_ids:
                if vnfd_id not in rift_vnfds:
                    raise VNFNotFoundError("VNF id %s not provided" % vnfd_id)

        openmano_nsd_im_body = json.loads(rift_nsd.from_dict())
        openmano_nsd_api_format = {
                                    "nsd:nsd-catalog": {
                                        "nsd": [openmano_nsd_im_body['nsd-catalog']['nsd'][0]]
                                    }
                                }

        openmano_nsd = http_api.post_nsd_v3(openmano_nsd_api_format)
        
        return openmano_nsd
        
    except Exception as e:
        logger.error(e)
        raise e

def rift2openmano_vnfd_nsd(rift_nsd, rift_vnfds, openmano_vnfd_ids, http_api, rift_vnfd_id=None):
    try:
        if rift_vnfd_id not in rift_vnfds:
                raise VNFNotFoundError("VNF id %s not provided" % rift_vnfd_id)

        # This is the scaling NSD Descriptor. Can use the NSD IM Model.
        openmano_nsd_im_body = json.loads(rift_nsd.from_dict())

        openmano_nsd_api_format = {
                                    "nsd:nsd-catalog": {
                                        "nsd": [openmano_nsd_im_body['nsd-catalog']['nsd'][0]]
                                    }
                                }

        openmano_nsd = http_api.post_nsd_v3(openmano_nsd_api_format)
        
        return openmano_nsd

    except Exception as e:
        logger.error(e)
        raise e


def cloud_init(rift_vnfd_id, vdu, project_name='default'):
    """ Populate cloud-init with script from
         either the inline contents or from the file provided
    """
    vnfd_package_store = rift.package.store.VnfdPackageFilesystemStore(logger, project=project_name)

    cloud_init_msg = None
    if 'cloud-init' in vdu:
        logger.debug("cloud-init script provided inline %s", vdu['cloud-init'])
        cloud_init_msg = vdu['cloud-init']
    elif 'cloud-init-file' in vdu:
    # Get cloud-init script contents from the file provided in the cloud_init_file param
        logger.debug("cloud-init script provided in file %s", vdu['cloud-init-file'])
        filename = vdu['cloud-init-file']
        vnfd_package_store.refresh()
        stored_package = vnfd_package_store.get_package(rift_vnfd_id)
        cloud_init_extractor = rift.package.cloud_init.PackageCloudInitExtractor(logger)
        try:
            cloud_init_msg = cloud_init_extractor.read_script(stored_package, filename)
        except rift.package.cloud_init.CloudInitExtractionError as e:
            raise ValueError(e)
    else:
        logger.debug("VDU translation: cloud-init script not provided")
        return

    logger.debug("Current cloud init msg is {}".format(cloud_init_msg))
    return cloud_init_msg

def config_file_init(rift_vnfd_id, vdu, cfg_file, project_name='default'):
    """ Populate config file init with file provided
    """
    vnfd_package_store = rift.package.store.VnfdPackageFilesystemStore(logger, project=project_name)

    # Get script contents from the file provided in the cloud_init directory
    logger.debug("config file script provided in file {}".format(cfg_file))
    filename = cfg_file
    vnfd_package_store.refresh()
    stored_package = vnfd_package_store.get_package(rift_vnfd_id)
    cloud_init_extractor = rift.package.cloud_init.PackageCloudInitExtractor(logger)
    try:
            cfg_file_msg = cloud_init_extractor.read_script(stored_package, filename)
    except rift.package.cloud_init.CloudInitExtractionError as e:
            raise ValueError(e)

    logger.debug("Current config file msg is {}".format(cfg_file_msg))
    return cfg_file_msg

def rift2openmano_vnfd(rift_vnfd, rift_nsd, http_api, project):
    try:
        openmano_vnfd_im_body = json.loads(rift_vnfd.from_dict())
        
        # All type_yang leafs renamed to type
        
        vnfd_dict = openmano_vnfd_im_body['vnfd-catalog']['vnfd'][0]
        
        if 'vdu' in vnfd_dict:
            for vdu in vnfd_dict['vdu']:
                if 'cloud-init-file' in vdu:
                    # Replacing the leaf with the actual contents of the file.
                    # The RO does not have the ability to read files yet.
                    vdu['cloud-init-file'] = cloud_init(vnfd_dict['id'], vdu, project)
                elif 'cloud-init' in vdu:
                    vdu['cloud-init'] = cloud_init(vnfd_dict['id'], vdu, project)

                if 'supplemental-boot-data' in vdu:
                    if 'config-file' in vdu['supplemental-boot-data']:
                        for config_file in vdu['supplemental-boot-data']['config-file']:
                            # Replacing the leaf with the actual contents of the file.
                            # The RO does not have the ability to read files yet.
                            config_file['source'] = config_file_init(vnfd_dict['id'], vdu, config_file['source'], project)
        
        openmano_vnfd_api_format = {
                                    "vnfd:vnfd-catalog": {
                                        "vnfd": [vnfd_dict]
                                    }
                                }
        openmano_vnfd = http_api.post_vnfd_v3(openmano_vnfd_api_format)
        
        return openmano_vnfd

    except Exception as e:
        logger.error(e)
        raise e



def parse_args(argv=sys.argv[1:]):
    """ Parse the command line arguments

    Arguments:
        arv - The list of arguments to parse

    Returns:
        Argparse Namespace instance
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o', '--outdir',
        default='-',
        help="Directory to output converted descriptors. Default is stdout",
        )

    parser.add_argument(
        '-n', '--nsd-file-hdl',
        metavar="nsd_file",
        type=argparse.FileType('r'),
        help="Rift NSD Descriptor File",
        )

    parser.add_argument(
        '-v', '--vnfd-file-hdls',
        metavar="vnfd_file",
        action='append',
        type=argparse.FileType('r'),
        help="Rift VNFD Descriptor File",
        )

    args = parser.parse_args(argv)

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    if not is_writable_directory(args.outdir):
        logging.error("Directory %s is not writable", args.outdir)
        sys.exit(1)

    return args


def write_yaml_to_file(name, outdir, desc_dict):
    file_name = "%s.yaml" % name
    yaml_str = yaml.dump(desc_dict)
    if outdir == "-":
        sys.stdout.write(yaml_str)
        return

    file_path = os.path.join(outdir, file_name)
    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with open(file_path, "w") as hdl:
        hdl.write(yaml_str)

    logger.info("Wrote descriptor to %s", file_path)


def main(argv=sys.argv[1:]):
    args = parse_args(argv)
    nsd = None
    openmano_vnfr_ids = dict()
    vnf_dict = None
    if args.vnfd_file_hdls is not None:
        vnf_dict = create_vnfd_from_files(args.vnfd_file_hdls)

    for vnfd in vnf_dict:
        openmano_vnfr_ids[vnfd] = vnfd

    if args.nsd_file_hdl is not None:
        nsd = create_nsd_from_file(args.nsd_file_hdl)

    openmano_nsd = rift2openmano_nsd(nsd, vnf_dict, openmano_vnfr_ids)
    vnfd_nsd = rift2openmano_vnfd_nsd(nsd, vnf_dict, openmano_vnfr_ids)
    write_yaml_to_file(openmano_nsd["name"], args.outdir, openmano_nsd)
    write_yaml_to_file(vnfd_nsd["name"], args.outdir, vnfd_nsd)

    for vnf in vnf_dict.values():
        openmano_vnf = rift2openmano_vnfd(vnf, nsd)
        write_yaml_to_file(openmano_vnf["vnf"]["name"], args.outdir, openmano_vnf)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    main()
