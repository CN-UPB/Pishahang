#!/bin/bash
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
# Author(s): Karun Ganesharatnam
# Creation Date: 02/26/2016
# 
source $RIFT_INSTALL/usr/rift/systemtest/util/mano/mano_common.sh

# Helper script for invoking the mission control system test using the systest_wrapper

SCRIPT_TEST="py.test -x -vvv \
            ${PYTEST_DIR}/system/test_launchpad.py \
            ${PYTEST_DIR}/multi_vm_vnf/test_multi_vm_vnf_trafgen.py \
            ${PYTEST_DIR}/multi_vm_vnf/test_trafgen_data.py"

test_cmd=""

# Parse command-line argument and set test variables
parse_args "${@}"

# Construct the test command based on the test variables and create the mvv image
mvv=true
create_mvv_image_file
construct_test_command

# Execute from pytest root directory to pick up conftest.py
cd "${PYTEST_DIR}"

eval ${test_cmd}
