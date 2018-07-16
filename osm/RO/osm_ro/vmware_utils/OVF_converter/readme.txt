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

This README file explains how to use OVF Converter Tool to generate OVF file from .qcow2, .img (raw) disk images.

CONTENTS OF THIS FILE
=====================
This readme file contains the following sections:

o Introduction
o Tool Requirements
o Installation
o Usage
o Trouble shooting
o Release History


Introduction
==================
OVF Converter Tool is a Command Line Interface (CLI) basically designed to generate OVF files from disk image such as .qcow2, and .img (raw format) which are other than .vmdk. 
Given a path to .qcow2 image this tool can generate .vmdk and .ovf files.
User can optionally specify name and location of ovf file. Also, one can use command line options to give disk size (GB), memory (MB), number of cpus, OS type, disk controller required for VM which will get deployed using generated OVF.
Generated OVF file can be used to deploy VM in Vmware vSphere or vCloud Director.

Note- Currently this tool supports only Ubuntu platform.


Tool Requirements
==================

This tool requires the following software package:
o	apt-get package manager
o	qemu-utils
o	python 2.7
o	python-lxml
o	libxml2-dev 
o	libxslt-dev 
o	python-dev 
o	python-pip
	 
Install.sh script in this folder will install all of these
software packages.


Installation
==================
User needs root privileges to install OVF Generator Tool.
Follow below setups for installation of OVF Converter Tool.
1. Make install.sh script in this folder executable by running below command
   chmod a+x install.sh
2. Run install.sh script as:
   ./install.sh
   
   Sample output -
		#################################################################
		#####             Installing Require Packages             #####
		#################################################################
		Hit:1 http://us.archive.ubuntu.com/ubuntu xenial InRelease
		Get:2 http://us.archive.ubuntu.com/ubuntu xenial-updates InRelease [102 kB]
		Get:3 http://security.ubuntu.com/ubuntu xenial-security InRelease [102 kB]
		Get:4 http://us.archive.ubuntu.com/ubuntu xenial-backports InRelease [102 kB]
		Fetched 306 kB in 1s (286 kB/s)
		Reading package lists... Done
		Reading package lists... Done
		Building dependency tree
		Reading state information... Done
		Note, selecting 'libxslt1-dev' instead of 'libxslt-dev'
		libxslt1-dev is already the newest version (1.1.28-2.1).
		python-dev is already the newest version (2.7.11-1).
		python-lxml is already the newest version (3.5.0-1build1).
		libxml2-dev is already the newest version (2.9.3+dfsg1-1ubuntu0.1).

		t version (1:2.5+dfsg-5ubuntu10.6).
		0 upgraded, 0 newly installed, 0 to remove and 72 not upgraded.

		#################################################################
		#####             Done                                #####
		#################################################################
		root@ubuntu:/home/vmware/OVF_converter#
		root@ubuntu:/home/vmware/OVF_converter#
     
3. Now tool is installed at /usr/local/bin and available for all users
4. User can access commands of OVF Generator Tool as:
    ovf_converter path [output location] [ovf name][memory][cpu][disk][ostype][disk_controller]


Usage
===================
o	Get version of tool as:

	Command -      ovf_converter -v
	Sample output -
				root@ubuntu:/home/vmware/OVF_converter# ovf_converter -v
				1.0 - Initial Realse
				root@ubuntu:/home/vmware/OVF_converter#

o	See all command line options of tool as:
	Command -       ovf_converter -h
	Sample output -
				root@ubuntu:/home/vmware/OVF_converter#
				root@ubuntu:/home/vmware/OVF_converter# ovf_converter -h
				Usage: ovf_converter_cli.py [-h] [-v] [-o OUTPUT_LOCATION] [-n OVF_NAME]
                            [-m MEMORY] [-c CPU] [-d DISK] [-s OSTYPE]
                            [-dc DISK_CONTROLLER]
                            path

				OVF converter to convert .qcow2 or raw image into OVF
				
				positional arguments:
				  path                  absolute path to source image which will get convert
				                        into ovf
				
				optional arguments:
				  -h, --help            show this help message and exit
				  -v, --version         shows version of OVF Converter tool
				  -o OUTPUT_LOCATION, --output_location OUTPUT_LOCATION
				                        location where created OVF will be kept. This location
				                        should have write access. If not given file will get
				                        created at source location (optional)
				  -n OVF_NAME, --ovf_name OVF_NAME
				                        name of output ovf file. If not given source image
				                        name will be used (optional)
				  -m MEMORY, --memory MEMORY
				                        required memory for VM in MB (default 1 GB)(optional)
				  -c CPU, --cpu CPU     required number of virtual cpus for VM (default 1 cpu)
				                        (optional)
				  -d DISK, --disk DISK  required size of disk for VM in GB (default as
				                        in source disk img) (optional)
				  -s OSTYPE, --osType OSTYPE
				                        required operating system type as specified in user
				                        document (default os type other 32 bit) (optional)
				  -dc DISK_CONTROLLER, --disk_Controller DISK_CONTROLLER
				                        required disk controller type (default controller SCSI
				                        with lsilogicsas) (SATA, IDE, Paravirtual, Buslogic,
				                        lsilogic, lsilogicsas) (optional)

				  
o	Create OVF file from qcow2 or raw disk image as:
	Command -     ovf_converter /home/vmware/centos_ovf/CentOS-7-x86_64-GenericCloud-1503.qcow2 -n centos_qcow2.ovf -m 2048 -c 4 -d 10 -s "Centos 32-bit" -dc "SATA"
	Sample output -
				root@ubuntu:/home/vmware/OVF_converter# ovf_converter /home/vmware/centos_ovf/CentOS-7-x86_64-GenericCloud-1503.qcow2 -n centos_qcow2.ovf -m 2048 -c 4 -d 10
				#### Start OVF conversion ####
				Getting source image information
				Converting source disk image to .vmdk                                                                         
				.....................................................
				Creating OVF
				Output OVF is at:  /home/vmware/centos_ovf/centos_qcow2.ovf
				#### Completed OVF conversion ####


Trouble shooting
==================
After installation of tool logs will get created at /usr/local/bin/OVF_converter/logs/ovf_converter.log file.
User can use these logs for debugging or trouble shooting.


Release History
===============

Version 1.0
-------------

Initial release  
