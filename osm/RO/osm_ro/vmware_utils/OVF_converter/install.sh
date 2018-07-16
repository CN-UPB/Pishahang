#!/usr/bin/env bash

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

echo '
 #################################################################
 #####             Installing Require Packages             #####
 #################################################################'

# Paths to copy application files
Install_dir="/usr/local/bin"
App_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
App_CLI_path="${App_dir}/format_converter/ovf_converter_cli.py"
Install_CLI_path="${Install_dir}/OVF_converter/format_converter/ovf_converter_cli.py"
Logs_Folder="${Install_dir}/OVF_converter/logs"
Log_Path="${Install_dir}/OVF_converter/logs/ovf_converter.log"

#Function to install packages using apt-get
function install_packages(){
      [ -x /usr/bin/apt-get ] && apt-get install -y $*
       
       #check properly installed
       for PACKAGE in $*
       do
           PACKAGE_INSTALLED="no"
           [ -x /usr/bin/apt-get ] && dpkg -l $PACKAGE            &>> /dev/null && PACKAGE_INSTALLED="yes"
           if [ "$PACKAGE_INSTALLED" = "no" ]
           then
               echo "failed to install package '$PACKAGE'. Revise network connectivity and try again" >&2
               exit 1
          fi
       done
   }
  
apt-get update  # To get the latest package lists
install_packages "libxml2-dev libxslt-dev python-dev python-pip python-lxml python-yaml"
install_packages "qemu-utils"

#apt-get install <package name> -y

#Move OVF Converter to usr/bin
cp -R "${App_dir}"   "${Install_dir}"

#Create logs folder and file
mkdir "${Logs_Folder}"
touch "${Log_Path}"

#Change permission
chmod -R 777 $Install_CLI_path
chmod -R 777 $Log_Path

touch "${Install_dir}/ovf_converter"
echo  "#!/bin/sh" > "${Install_dir}/ovf_converter"
echo  "python ${Install_CLI_path} \"\$@\"" >> "${Install_dir}/ovf_converter"
chmod a+x "${Install_dir}/ovf_converter"

echo '	
 #################################################################
 #####             Done                                #####
 #################################################################'
