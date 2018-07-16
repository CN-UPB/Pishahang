# 
#   Copyright 2016-2017 RIFT.IO Inc
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
# Author(s): Austin Cormier
# Creation Date: 2015/11/20
# 

##
# Yang targets
##

rift_add_yang_target(
  TARGET rwsdn_yang
  YANG_FILES rw-sdn.yang
  COMPONENT ${INSTALL_COMPONENT}
  LIBRARIES
    rwsdnal_yang_gen
  DEPENDS
    rwsdnal_yang
  ASSOCIATED_FILES
    rw-sdn.role.xml
)

rift_add_yang_target(
  TARGET rwcloud_yang
  YANG_FILES rw-cloud.yang 
  COMPONENT ${INSTALL_COMPONENT}
  LIBRARIES
    rwsdn_yang_gen
    rwcal_yang_gen
    rwprojectmano_yang_gen
    mano-types_yang_gen
  DEPENDS
    rwcal_yang
    rwsdnal_yang
  ASSOCIATED_FILES
    rw-cloud.role.xml
)

rift_add_yang_target(
  TARGET rwconfig_agent_yang
  YANG_FILES rw-config-agent.yang
  COMPONENT ${INSTALL_COMPONENT}
  LIBRARIES
    rwcal_yang_gen
    rwprojectmano_yang_gen
  DEPENDS
    rwcal_yang
    rwprojectmano_yang
  ASSOCIATED_FILES
    rw-config-agent.role.xml
)

rift_add_yang_target(
  TARGET rwro_account_yang
  YANG_FILES rw-ro-account.yang
  COMPONENT ${INSTALL_COMPONENT}
  LIBRARIES
    rwprojectmano_yang_gen
    mano-types_yang_gen
  DEPENDS
    rwprojectmano_yang
  ASSOCIATED_FILES
    rw-ro-account.role.xml
)
