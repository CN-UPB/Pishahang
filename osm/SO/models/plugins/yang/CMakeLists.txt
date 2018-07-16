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
# Author(s): Anil Gunturu
# Creation Date: 10/15/2014
# 

# NOTE: These files will be used by the new MANO subsystem
set(source_yang_files
  ietf-l2-topology.yang
  ietf-network-topology.yang
  ietf-network.yang
  nsd-base.yang rw-nsd-base.yang
  nsd.yang rw-nsd.yang
  project-nsd.yang rw-project-nsd.yang
  nsr.yang rw-nsr.yang
  pnfd.yang
  rw-topology.yang
  vld.yang rw-vld.yang
  vlr.yang rw-vlr.yang
  vnfd-base.yang rw-vnfd-base.yang
  vnfd.yang rw-vnfd.yang
  project-vnfd.yang rw-project-vnfd.yang
  vnfr.yang rw-vnfr.yang
  mano-rift-groupings.yang
  vnffgd.yang
  )

rift_add_yang_target(
  TARGET mano-types_yang
  YANG_FILES
    mano-types.yang
  COMPONENT ${INSTALL_COMPONENT}
  LIBRARIES
    rwprojectmano_yang_gen
  )

rift_add_yang_target(
  TARGET mano_yang
  YANG_FILES ${source_yang_files}
  GIR_PATHS ${CMAKE_CURRENT_BINARY_DIR}
  COMPONENT ${INSTALL_COMPONENT}
  LIBRARIES
    rwmanifest_yang_gen
    rwschema_yang_gen
    rwcloud_yang_gen
    rwro_account_yang_gen
    rwsdn_yang_gen
    rwconfig_agent_yang_gen
    mano-types_yang_gen
    rwprojectmano_yang_gen
  DEPENDS
    rwcloud_yang
    rwro_account_yang
    rwsdn_yang
    rwconfig_agent_yang
    rwprojectmano_yang
  ASSOCIATED_FILES
    project-vnfd.role.xml
    project-nsd.role.xml
    vnfr.role.xml
    rw-vnfr.role.xml
    vlr.role.xml
    nsr.role.xml
  )

#rift_gen_yang_tree(mano-pyang-trees
#  OUTFILE_PREFIX mano.yang
#  YANG_FILES
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/vnfd.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/vld.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/nsd.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/rw-vnfd.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/rw-vld.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/rw-nsd.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/pnfd.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/vnffgd.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/ietf-network.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/ietf-network-topology.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/ietf-l2-topology.yang
#    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/plugins/yang/rw-topology.yang
#  )
