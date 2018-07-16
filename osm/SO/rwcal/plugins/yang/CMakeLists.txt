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
# 

##
# Parse the yang files
##

include(rift_yang)

set(source_yang_files rwcal.yang)

rift_generate_python_log_yang(
    LOG_CATEGORY_NAME rw-cal-log
    START_EVENT_ID 63000
    OUT_YANG_FILE_VAR rw_cal_log_file
    )

rift_add_yang_target(
  TARGET rwcal_yang
  YANG_FILES
    ${source_yang_files}
    ${rw_cal_log_file}
  COMPONENT ${INSTALL_COMPONENT}
  DEPENDS
    mano-types_yang
    rwprojectmano_yang
  LIBRARIES
    rwschema_yang_gen
    rwyang
    rwlog
    rwlog-mgmt_yang_gen
    mano-types_yang_gen
    rwprojectmano_yang_gen
)
