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
# Author(s): Manish Patel
# Creation Date: 10/28/2015
# 

cmake_minimum_required(VERSION 2.8)

set(CONMAN_INSTALL "demos/conman")

install(
  FILES
    start_cm_system.py
    README.start_cm
  DESTINATION ${CONMAN_INSTALL}
  COMPONENT ${INSTALL_COMPONENT}
)
  
# set(NS_NAME ping_pong_nsd)
# install(
#   FILES
#     ${NS_NAME}/configuration_input_params.yml
#     ${NS_NAME}/ping_vnfd_1_scriptconf_template.cfg
#     ${NS_NAME}/pong_vnfd_11_scriptconf_template.cfg
#   DESTINATION ${CONMAN_INSTALL}/${NS_NAME}
#   COMPONENT ${INSTALL_COMPONENT}
# )

