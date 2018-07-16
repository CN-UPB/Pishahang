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
# Author(s): Tom Seidenberg
# Creation Date: 2014/04/08
# 

set(source_yang_files
  rw-launchpad.yang
  rw-monitor.yang
  rw-nsm.yang
  rw-resource-mgr.yang
  rw-vnfm.yang
  rw-vns.yang
  rw-image-mgmt.yang
  rw-pkg-mgmt.yang
  rw-staging-mgmt.yang
  )

##
# Yang targets
##
rift_generate_python_log_yang(
    LOG_CATEGORY_NAME rw-mano-log
    START_EVENT_ID 65000
    OUT_YANG_FILE_VAR rw_mano_log_file
    )

rift_generate_python_log_yang(
    LOG_CATEGORY_NAME rw-monitor-log
    START_EVENT_ID 64000
    OUT_YANG_FILE_VAR rw_monitor_log_file
    )

rift_generate_python_log_yang(
    LOG_CATEGORY_NAME rw-mon-params-log
    START_EVENT_ID 67000
    OUT_YANG_FILE_VAR rw_mon_params_log_file
    )

rift_generate_python_log_yang(
    LOG_CATEGORY_NAME rw-resource-mgr-log
    START_EVENT_ID 69000
    OUT_YANG_FILE_VAR rw_resource_mgr_log_file
    )

rift_add_yang_target(
  TARGET rwlaunchpad_yang
  YANG_FILES
    ${source_yang_files}
    ${rw_mano_log_file}
    ${rw_monitor_log_file}
    ${rw_mon_params_log_file}
    ${rw_resource_mgr_log_file}
  COMPONENT ${INSTALL_COMPONENT}
  LIBRARIES
    mano_yang_gen
    rwcloud_yang_gen
    rwro_account_yang_gen
    rw_conman_yang_gen
    rwconfig_agent_yang_gen
    mano-types_yang_gen
    rwprojectmano_yang_gen
  DEPENDS
    mano_yang
    rwcloud_yang
    rwro_account_yang
    rw_conman_yang
    rwconfig_agent_yang
    mano-types_yang
    rwprojectmano_yang
    # Added to make sure that the target is built,
    # Not required b mano yang
    rw_project_person_yang
  ASSOCIATED_FILES
    rw-pkg-mgmt.role.xml
    rw-staging-mgmt.role.xml
    rw-image-mgmt.role.xml
)

rift_add_yang_target(
  TARGET rw_project_person_yang
  YANG_FILES
    rw-project-person-db.yang
  COMPONENT ${INSTALL_COMPONENT}
  LIBRARIES
    rwprojectmano_yang_gen
  DEPENDS
    rwprojectmano_yang
  ASSOCIATED_FILES
    rw-launchpad.role.xml
)
