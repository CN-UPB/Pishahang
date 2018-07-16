#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# Copyright 2016-2017 VMware Inc.
# This file is part of ETSI OSM
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact:  osslegalrouting@vmware.com
##

import argparse
from converter import OVFConverter , get_version

def execute_cli():

    """
        Method to parse CLI arguments and execute commands accordingly
        Args : None
        Return : None
    """
    parser = argparse.ArgumentParser(description='OVF converter to convert .qcow2 or raw image into OVF')

    parser.add_argument("-v","--version", action="version", version=str(get_version()),
                            help="shows version of OVF Converter tool")

    parser.add_argument("path", action="store",
                            help=" absolute path to source image which will get convert into ovf")

    parser.add_argument("-o", "--output_location", action="store",
                            help="location where created OVF will be kept. This location "\
                                  "should have write access. If not given file will get "\
                                  "created at source location  (optional)")

    parser.add_argument("-n","--ovf_name", action="store",
                            help="name of output ovf file. If not given source image name will "\
                            " be used (optional)")

    parser.add_argument("-m","--memory", action="store",
                            help="required memory for VM in MB (default 1 GB)(optional)")

    parser.add_argument("-c","--cpu", action="store",
                            help="required number of virtual cpus for VM (default 1 cpu) (optional)")

    parser.add_argument("-d","--disk", action="store",
                            help="required size of disk for VM in GB "\
                            "(default as in source disk img) (optional)")

    parser.add_argument("-s","--osType", action="store",
                            help="required operating system type as specified "\
                            "in user document (default os type other 32 bit) (optional)")

    parser.add_argument("-dc","--disk_Controller", action="store",
                            help="required disk controller type "\
                            " (default controller SCSI with lsilogicsas) "\
                            "(SATA, IDE, Paravirtual, Buslogic, Lsilogic, Lsilogicsas) (optional)")

    args = parser.parse_args()

    if args.path:
        con = OVFConverter(args.path,
                           output_location=args.output_location,
                           output_ovf_name=args.ovf_name,
                           memory=args.memory,
                           cpu=args.cpu,
                           disk=args.disk,
                           os_type=args.osType,
                           disk_controller=args.disk_Controller,
                           )

        print("#### Start OVF conversion  ####")
        con.create_ovf()
        print("#### Completed OVF conversion  ####")


if __name__ == "__main__":
    execute_cli()

