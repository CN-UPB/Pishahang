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

import logging
import os
import subprocess
import yaml
from lxml import etree as ET
from command_progress import CommandProgressbar

#file paths
MODULE_DIR = os.path.dirname(__file__)
OVF_TEMPLATE_PATH = os.path.join(os.path.dirname(MODULE_DIR),
                                "ovf_template/template.xml")
OS_INFO_FILE_PATH = os.path.join(os.path.dirname(MODULE_DIR), 
                                "config/os_type.yaml")
DISK_CONTROLLER_INFO_FILE_PATH = os.path.join(os.path.dirname(MODULE_DIR),
                                              "config/disk_controller.yaml")


#Set logger
LOG_FILE = os.path.join(os.path.dirname(MODULE_DIR),"logs/ovf_converter.log")
logger = logging.getLogger(__name__)
hdlr = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(10)

__version__ = "1.0"
__description__ = "initial Release"

def get_version(*args, **kwargs):
    """ get version of this application"""
    version = str(__version__ ) +" - "+ str( __description__ )
    return version

#converter class
class OVFConverter(object):
    """ Class to convert input image into OVF format """

    def __init__(self, source_img_path, output_location=None, output_ovf_name=None,
                    memory=None, cpu=None, disk=None, os_type=None,
                    disk_controller=None,
                    options={'subformat':'streamOptimized'}):
        """
            Constructor to initialize object of class OVFConverter
            Args:
            source_img_path - absolute path to source image which will get convert into ovf
            output_location - location where created OVF will be kept. This location
                              should have write access. If not given file will get
                              created at source location  (optional)
            output_ovf_name - name of output ovf.If not given source image name will 
                              be used (optional)
            memory -          required memory for VM in MB (optional)
            cpu -             required number of virtual cpus for VM (optional)
            disk -            required size of disk for VM in GB (optional)
            os_type-          required operating system type as specified in user document
                                (default os type other 32 bit) (optional)
            disk_controller - required disk controller type
                                (default controller SCSI with lsilogicsas)
                                (SATA, IDE, Paravirtual, Buslogic, Lsilogic, Lsilogicsas) (optional)
            options - subformat option for OVF  (optional)

            Returns:
                Nothing.
        """
        self.logger = logger
        self.ovf_template_path = OVF_TEMPLATE_PATH

        self.source_img_path = source_img_path
        file_location, file_extension = os.path.splitext(self.source_img_path)
        self.source_img_location = os.path.dirname(self.source_img_path)
        self.source_format = file_extension[1:]
        self.source_img_filename = os.path.basename(self.source_img_path).split('.')[0]

        self.output_format = "ovf"
        self.output_ovf_name = output_ovf_name.split('.')[0] if output_ovf_name else self.source_img_filename
        self.output_location = output_location if output_location else self.source_img_location
        self.output_ovf_name_ext = self.output_ovf_name + "." + self.output_format
        self.output_path = os.path.join(self.output_location , self.output_ovf_name_ext )

        self.output_diskimage_format = "vmdk"
        self.output_diskimage_name = self.source_img_filename + "."+ self.output_diskimage_format
        self.output_diskimage_path = os.path.join(self.output_location,  self.output_diskimage_name)


        self.logger.info("Input parameters to Converter: \n ovf_template_path = {}, \n source_img_path = {}, \n"\
                    "source_img_location ={} , \n source_format = {}, \n source_img_filename = {}".format(
                                                        self.ovf_template_path,
                                                        self.source_img_path, self.source_img_location,
                                                        self.source_format, self.source_img_filename ))

        self.logger.info("Output parameters to Converter: \n output_format = {}, \n output_ovf_name = {}, \n"\
                    "output_location ={} , \n output_path = {}, \n output_diskimage_name = {} , \n"\
                    " output_diskimage_path = {} ".format(self.output_format, self.output_ovf_name,
                                                    self.output_location, self.output_path,
                                                    self.output_diskimage_name,self.output_diskimage_path ))


        self.disk_capacity = 1
        self.disk_populated_size = 0

        self.vm_name = self.output_ovf_name
        self.memory = str(memory) if memory is not None else None
        self.cpu = str(cpu) if cpu is not None else None
        self.os_type=str(os_type).strip() if os_type else None

        if self.os_type:
            self.osID , self.osType = self.__get_osType()
            if self.osID is None or self.osType is None:
               error_msg = "ERROR: Invalid input can not find OS type {} ".format(self.os_type)
               self.__raise_exception(error_msg)

        self.disk_controller = str(disk_controller).strip() if disk_controller else None

        if self.disk_controller:
            self.disk_controller_info = self.__get_diskcontroller()

            if not self.disk_controller_info:
                error_msg = "ERROR: Invalid input can not find Disk Controller {} ".format(self.disk_controller)
                self.__raise_exception(error_msg)

        if disk is not None:
            #convert disk size from GB to bytes
            self.disk_size = int(disk) * 1024 * 1024 * 1024
        else:
            self.disk_size = None

        self.logger.info("Other input parameters to Converter: \n vm_name = {}, \n memory = {}, \n"\
                    "disk_size ={} \n os type = {} \n disk controller = {}".format(
                                self.vm_name, self.memory, self.disk_size, self.os_type, self.disk_controller
                                ))

        #check access for read input location and write output location return none if no access
        if not os.access(self.source_img_path, os.F_OK):
            error_msg = "ERROR: Source image file {} not present".format(self.source_img_path)
            self.__raise_exception(error_msg, exception_type="IO")

        elif not os.access(self.source_img_path, os.R_OK):
            error_msg = "ERROR: Cannot read source image file {}".format(self.source_img_path)
            self.__raise_exception(error_msg, exception_type="IO")

        if not os.access(self.output_location, os.W_OK):
            error_msg = "ERROR: Not have write access to location {} to write output OVF ".format(self.source_img_path)
            self.__raise_exception(error_msg, exception_type="IO")

    def __get_image_info(self):
        """ 
            Private method to get information about source imager.
            Args  : None
            Return : True on success else False
        """
        try:
            print("Getting source image information")
            command = "qemu-img info \t " + self.source_img_path
            output, error, returncode= self.__execute_command(command)

            if error or returncode:
                self.logger.error("ERROR: Error occurred while getting information about source image : {} \n "\
                                  "return code : {} ".format(error, returncode))
                return False

            elif output:
                self.logger.info("Get Image Info Output : {} \n ".format(output))
                split_output = output.split("\n")
                for line in split_output:
                    line = line.strip()
                    if "virtual size" in line:
                        virtual_size_info = line.split(":")[1].split()
                        if len(virtual_size_info) == 3 and virtual_size_info[2].strip(")") == "bytes":
                            self.disk_capacity  = int(virtual_size_info[1].strip("("))
                        else:
                            self.disk_capacity  = self.__convert_size(virtual_size_info[0])

                    elif "disk size" in line:
                        size = line.split(":")[1].split()[0]
                        self.disk_populated_size = self.__convert_size(size)
                    elif "file format" in line:
                        self.source_format = line.split(":")[1]

                self.logger.info("Updated source image virtual disk capacity : {} ,"\
                                 "Updated source image populated size: {}".format(self.disk_capacity,
                                                                    self.disk_populated_size))
                return True
        except Exception as exp:
            error_msg = "ERROR: Error occurred while getting information about source image : {}".format(exp)
            self.logger.error(error_msg)
            print(error_msg)
            return False

    def __convert_image(self):
        """ 
            Private method to convert source disk image into .vmdk disk image.
            Args  : None
            Return : True on success else False
        """

        print("Converting source disk image to .vmdk ")

        progress = CommandProgressbar()
        progress.start_progressbar()

        command = "qemu-img convert -f "+ self.source_format +" -O " + self.output_diskimage_format + \
                " -o subformat=streamOptimized " + self.source_img_path + "\t" + self.output_diskimage_path

        output, error , returncode = self.__execute_command(command)

        progress.stop_progressbar()

        if error or returncode :
            error_msg = "ERROR: Error occurred while converting source disk image into vmdk : {} \n "\
                                  "return code : {} ".format(error, returncode)
            self.logger.error(error_msg)
            print(error_msg)
            return False
        else:
            if os.path.isfile(self.output_diskimage_path):
                self.logger.info("Successfully converted source image {} into {} \n "\
                                  "return code : {} ".format(self.source_img_path,
                                                        self.output_diskimage_path,
                                                        returncode))
                result = self.__make_image_bootable()
                if result:
                    self.logger.info("Made {} bootable".format(self.output_diskimage_path))
                    return True
                else:
                    self.logger.error("Cannot make {} bootable".format(self.output_diskimage_path))
                    print("ERROR: Fail to convert source image into .vmdk")
                    return False
            else:
                self.logger.error("Converted vmdk disk file {} is not present \n ".format(
                                                    self.output_diskimage_path))
                print("Fail to convert source image into .vmdk")
                return False

    def __make_image_bootable(self):
        """ 
            Private method to make source disk image bootable.
            Args  : None
            Return : True on success else False
        """
        command = "printf '\x03' | dd conv=notrunc of="+ self.output_diskimage_path + "\t bs=1 seek=$((0x4))"
        output, error, returncode = self.__execute_command(command)

        if error and returncode :
            error_msg = "ERROR:Error occurred while making source disk image bootable : {} \n "\
                                  "return code : {} ".format(error, returncode)
            self.logger.error(error_msg)
            print(error_msg)
            return False
        else:
            self.logger.info("Make Image Bootable Output : {} ".format(output))
            return True


    def __edit_ovf_template(self):
        """ 
            Private method to create new OVF file by editing OVF template
            Args  : None
            Return : True on success else False
        """
        try:
            print("\nCreating OVF")
            #Read OVF template file
            OVF_tree = ET.parse(self.ovf_template_path)
            root = OVF_tree.getroot()

            #Collect namespaces
            nsmap = {k:v for k,v in root.nsmap.iteritems() if k}
            nsmap["xmlns"]= "http://schemas.dmtf.org/ovf/envelope/1"

            #Edit OVF template
            references = root.find('xmlns:References',nsmap)
            if references is not None:
                file_tag = references.find('xmlns:File', nsmap)
                if file_tag is not None:
                    file_tag.attrib['{'+nsmap['ovf']+'}href'] = self.output_diskimage_name

            disksection = root.find('xmlns:DiskSection',nsmap)
            if disksection is not None:
                diak_tag = disksection.find('xmlns:Disk', nsmap)
                if diak_tag is not None:
                    if self.disk_size and self.disk_size > self.disk_capacity:
                        self.disk_capacity = self.disk_size
 
                    diak_tag.attrib['{'+nsmap['ovf']+'}capacity'] = str(self.disk_capacity)
                    diak_tag.attrib['{'+nsmap['ovf']+'}populatedSize'] = str(self.disk_populated_size)

            virtuasystem = root.find('xmlns:VirtualSystem',nsmap)
            if virtuasystem is not None:
                name_tag = virtuasystem.find('xmlns:Name', nsmap)
                if name_tag is not None:
                    name_tag.text = self.vm_name

                if self.os_type is not None:
                    operatingSystemSection = virtuasystem.find('xmlns:OperatingSystemSection', nsmap)
                    if self.osID and self.osType:
                        operatingSystemSection.attrib['{'+nsmap['ovf']+'}id'] = self.osID
                        os_discription_tag = operatingSystemSection.find('xmlns:Description', nsmap)
                        os_discription_tag.text = self.osType

                virtualHardwareSection = virtuasystem.find('xmlns:VirtualHardwareSection', nsmap)
                system = virtualHardwareSection.find('xmlns:System', nsmap)
                virtualSystemIdentifier = system.find('vssd:VirtualSystemIdentifier', nsmap)
                if virtualSystemIdentifier is not None:
                    virtualSystemIdentifier.text = self.vm_name

                if self.memory is not None or self.cpu is not None or self.disk_controller is not None:
                    for item in virtualHardwareSection.iterfind('xmlns:Item',nsmap):
                        description = item.find("rasd:Description",nsmap)

                        if self.cpu is not None:
                            if description is not None and description.text == "Number of Virtual CPUs":
                                cpu_item = item.find("rasd:VirtualQuantity", nsmap)
                                name_item = item.find("rasd:ElementName", nsmap)
                                if cpu_item is not None:
                                    cpu_item.text = self.cpu
                                    name_item.text = self.cpu+" virtual CPU(s)"

                        if self.memory is not None:
                            if description is not None and description.text == "Memory Size":
                                mem_item = item.find("rasd:VirtualQuantity", nsmap)
                                name_item = item.find("rasd:ElementName", nsmap)
                                if mem_item is not None:
                                    mem_item.text = self.memory
                                    name_item.text = self.memory + " MB of memory"

                        if self.disk_controller is not None:
                            if description is not None and description.text == "SCSI Controller":
                                if self.disk_controller_info is not None:
                                    name_item = item.find("rasd:ElementName", nsmap)
                                    name_item.text = str(self.disk_controller_info["controllerName"])+"0"

                                    resource_type = item.find("rasd:ResourceType", nsmap)
                                    resource_type.text = self.disk_controller_info["resourceType"]

                                    description.text = self.disk_controller_info["controllerName"]
                                    resource_subtype = item.find("rasd:ResourceSubType", nsmap)
                                    if self.disk_controller_info["controllerName"] == "IDE Controller":
                                        #Remove resource subtype item
                                        resource_subtype.getparent().remove(resource_subtype)
                                    if "resourceSubType" in  self.disk_controller_info:
                                        resource_subtype.text = self.disk_controller_info["resourceSubType"]

                #Save output OVF
            OVF_tree.write(self.output_path, xml_declaration=True,encoding='utf-8',
               method="xml" )

            if os.path.isfile(self.output_path):
                logger.info("Successfully written output OVF at {}".format(self.output_path))
                print("Output OVF is at :  {}".format(self.output_path))
                return self.output_path
            else:
                error_msg = "ERROR: Error occurred while creating OVF file"
                print(error_msg)
                return False

        except Exception as exp:
            error_msg = "ERROR: Error occurred while editing OVF template : {}".format(exp)
            self.logger.error(error_msg)
            print(error_msg)
            return False


    def __convert_size(self,size):
        """ 
            Private method to convert disk size from GB,MB to bytes.
            Args :
                size  : disk size with prefix 'G' for GB and 'M' for MB
            Return :  disk size in bytes
        """
        byte_size= 0
        try:
            if not size:
                self.logger.error("No size {} to convert in bytes".format(size))
            else:
                size = str(size)
                disk_size = float(size[:-1])
                input_type = size[-1].strip()

                self.logger.info("Disk size : {} , size type : {} ".format(disk_size,input_type))

                if input_type == "G":
                    byte_size = disk_size * 1024 * 1024 *1024
                elif input_type == "M":
                    byte_size = disk_size * 1024 * 1024

                self.logger.info("Disk size in bytes: {} ".format(byte_size))

            return int(byte_size)

        except Exception as exp:
            error_msg = "ERROR:Error occurred while converting disk size in bytes : {}".format(exp)
            self.logger.error(error_msg)
            print(error_msg)
            return False

    def __get_osType(self):
        """ 
            Private method to get OS ID and Type
            Args :
                None
            Return :
                osID : OS ID
                osType: OS Type
        """
        osID = None
        osType = None
        os_info = self.__read_yaml_file(OS_INFO_FILE_PATH)
        try:
            if self.os_type and os_info:
                for os_id , os_type in os_info.iteritems():
                    if self.os_type.lower() == os_type.lower():
                        osID = os_id
                        osType = os_type
                        break
        except Exception as exp:
            error_msg = "ERROR:Error occurred while getting OS details : {}".format(exp)
            self.logger.error(error_msg)
            print(error_msg)

        return osID, osType


    def __get_diskcontroller(self):
        """ 
            Private method to get details of Disk Controller
            Args :
                None
            Return :
                disk_controller : dict with details of Disk Controller
        """
        disk_controller = {}
        scsi_subtype = None
        if self.disk_controller.lower() in ["paravirtual", "lsilogic", "buslogic", "lsilogicsas"]:
            scsi_subtype = self.disk_controller
            self.disk_controller = "SCSI"

        disk_controller_info = self.__read_yaml_file(DISK_CONTROLLER_INFO_FILE_PATH)
        try:
            if self.disk_controller and disk_controller_info:
                for key , value in disk_controller_info.iteritems():
                    if self.disk_controller.lower() in key.lower():
                        disk_controller['controllerName'] = key
                        disk_controller['resourceType'] = str(value["ResourceType"])
                        resourceSubTypes = value["ResourceSubTypes"] if "ResourceSubTypes" in value else None
                        if key == "SATA Controller":
                            disk_controller["resourceSubType"] = resourceSubTypes[0]
                        elif key == "SCSI Controller":
                            if scsi_subtype:
                                if scsi_subtype.lower() == "paravirtual":
                                    scsi_subtype = "VirtualSCSI"
                                for subtype in resourceSubTypes:
                                    if scsi_subtype.lower() == subtype.lower():
                                        disk_controller["resourceSubType"] = subtype
                                        break
                                else:
                                    error_msg = "ERROR: Invalid inputs can not "\
                                    "find SCSI subtype {}".format(scsi_subtype)
                                    self.__raise_exception(error_msg)

        except KeyError as exp:
            error_msg = "ERROR:Error occurred while getting Disk Controller details : {}".format(exp)
            self.logger.error(error_msg)
            print(error_msg)

        return disk_controller

    def __read_yaml_file(self, file_path):
        """ 
            Private method to execute command
            Args :
                command  : command to execute
            Return :
                Dict of yaml data
        """
        with open(file_path) as data_file:    
            data = yaml.load(data_file)
        return data

    def __raise_exception(self, error_msg , exception_type="Generic"):
        """ 
            Private method to execute command
            Args :
                command  : command to execute
            Return :
               None
        """
        if error_msg:
            self.logger.debug(error_msg)
            print(error_msg)
            if exception_type == "Generic":
                raise Exception(error_msg)
            elif exception_type == "IO":
                raise Exception(error_msg)

    def __execute_command(self, command):
        """ 
            Private method to execute command
            Args :
                command  : command to execute
            Return :
                stdout : output of command
                stderr: error occurred while executing command if any
                returncode : return code of command execution
        """
        try:
            self.logger.info("Execute command: {} ".format(command))

            proc = subprocess.Popen(command , stdout = subprocess.PIPE, stdin = subprocess.PIPE,
                                             stderr = subprocess.PIPE,shell=True)
            stdout, stderr = proc.communicate()
            returncode = proc.returncode

        except Exception as exp:
            self.logger.error("Error {} occurred while executing command {} ".format(exp,command))

        return  stdout, stderr , returncode


    def create_ovf(self):
        """ 
            Method to convert source image into OVF
            Args : None
            Return : True on success else False
        """
        #check output format
        if self.source_format == self.output_format:
            self.logger.info("Source format is OVF. No need to convert: {} ")
            return self.source_img_path

        #Get source img properties
        img_info = self.__get_image_info()
        if img_info:

            #Create vmdk disk image
            disk_img = self.__convert_image()
            if disk_img:

                #Edit OVF tempalte
                ovf_path = self.__edit_ovf_template()
                return ovf_path
        else:
            self.logger.error("Error in getting image information cannot convert image")
            raise Exception("Error in getting image information cannot convert image")
            return False

