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

##
# Yang targets
##

rift_generate_python_log_yang(
    LOG_CATEGORY_NAME rw-conman-log
    START_EVENT_ID 66000
    OUT_YANG_FILE_VAR rw_conman_log_file
    )

rift_add_yang_target(
  TARGET rw_conman_yang
  YANG_FILES rw-conman.yang ${rw_conman_log_file}
  COMPONENT ${INSTALL_COMPONENT}
  LIBRARIES
    mano_yang_gen
    mano-types_yang_gen
    rwconfig_agent_yang_gen
  DEPENDS
    mano_yang
    rwconfig_agent_yang
    mano-types_yang
)


