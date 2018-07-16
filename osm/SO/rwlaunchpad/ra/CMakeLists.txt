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
# Author(s): Paul Laidler
# Creation Date: 09/16/2015
# 

cmake_minimum_required(VERSION 2.8)

install(
  PROGRAMS
    pingpong_accounts_systest
    pingpong_longevity_systest
    pingpong_vnf_systest
    pingpong_records_systest
    pingpong_vnf_reload_systest
    pingpong_lp_ha_systest
    pingpong_recovery_systest
    pingpong_floating_ip
    pingpong_scaling_systest
    pingpong_ha_systest
    pingpong_mro_systest
    pingpong_input_params_systest
    primitives_systest
    onboard_delete_vnfs_systest
    accounts_creation_onboard_instatiate_systest
    accounts_creation_onboard_instatiate_systest_repeat_option
    accounts_creation_onboard_systest
    scaling_systest
  DESTINATION usr/rift/systemtest/pingpong_vnf
  )

install(
  PROGRAMS
    multi_vm_vnf_slb_systest.sh
    multi_vm_vnf_trafgen_systest.sh
  DESTINATION usr/rift/systemtest/multi_vm_vnf
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  PROGRAMS
    rbac_basics_systest
    rbac_identity
    rbac_roles_systest
    rbac_usage_scenarios_systest
    rbac_mano_xpaths_access
    tbac_token
    complex_scaling
  DESTINATION usr/rift/systemtest/rbac
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  PROGRAMS
    gui_test_launchpad_ui
  DESTINATION usr/rift/systemtest/gui_tests
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  PROGRAMS
    ha_basics_systest
    ha_multiple_failovers_systest
  DESTINATION usr/rift/systemtest/ha
  COMPONENT ${PKG_LONG_NAME})

install(
  PROGRAMS
    accounts_creation_onboard_instatiate_systest
    l2port_chaining_systest
    metadata_vdud_systest
    ns_instantiate_memory_check_systest
  DESTINATION usr/rift/systemtest/mano
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    pytest/multivm_vnf/conftest.py
    pytest/multivm_vnf/test_multi_vm_vnf_slb.py
    pytest/multivm_vnf/test_multi_vm_vnf_trafgen.py
    pytest/multivm_vnf/test_trafgen_data.py
  DESTINATION usr/rift/systemtest/pytest/multi_vm_vnf
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  PROGRAMS
    launchpad_longevity_systest
    launchpad_systest
  DESTINATION usr/rift/systemtest/launchpad
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    racfg/multi_tenant_systest_openstack.racfg
  DESTINATION usr/rift/systemtest/launchpad
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    pytest/conftest.py
    pytest/test_launchpad.py
    pytest/test_launchpad_longevity.py
    pytest/test_start_standby.py
    pytest/test_failover.py
  DESTINATION usr/rift/systemtest/pytest/system
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    pytest/ns/conftest.py
    pytest/ns/test_onboard.py
    pytest/ns/test_multiple_ns_instantiation.py
  DESTINATION usr/rift/systemtest/pytest/system/ns
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    pytest/ns/pingpong/test_accounts_framework.py
    pytest/ns/pingpong/test_floating_ip.py
    pytest/ns/pingpong/test_ha_pingpong.py
    pytest/ns/pingpong/test_pingpong.py
    pytest/ns/pingpong/test_pingpong_longevity.py
    pytest/ns/pingpong/test_records.py
    pytest/ns/pingpong/test_scaling.py
    pytest/ns/pingpong/test_mro_pingpong.py
    pytest/ns/pingpong/test_input_params.py
  DESTINATION usr/rift/systemtest/pytest/system/ns/pingpong
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    pytest/ns/rbac/conftest.py
    pytest/ns/rbac/test_rbac.py
    pytest/ns/rbac/test_rbac_roles.py
    pytest/ns/rbac/test_rbac_identity.py
    pytest/ns/rbac/test_tbac_token.py
    pytest/ns/rbac/test_rbac_usages.py
    pytest/ns/rbac/test_rbac_mano_xpath_access.py
  DESTINATION usr/rift/systemtest/pytest/system/ns/rbac
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    pytest/ns/ha/conftest.py
    pytest/ns/ha/test_ha_basic.py
    pytest/ns/ha/test_ha_operations.py
    pytest/ns/ha/test_ha_multiple_failovers.py
  DESTINATION usr/rift/systemtest/pytest/system/ns/ha
  COMPONENT ${PKG_LONG_NAME})

install(
  FILES
    pytest/ns/gui_tests/conftest.py
    pytest/ns/gui_tests/test_launchpad_ui.py
  DESTINATION usr/rift/systemtest/pytest/system/ns/gui_tests
  COMPONENT ${PKG_LONG_NAME})

install(
  FILES
    pytest/ns/restapitest/test_project_restapi.py
  DESTINATION usr/rift/systemtest/pytest/system/ns/restapitest
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    pytest/ns/restapitest/utils/__init__.py
    pytest/ns/restapitest/utils/imports.py
    pytest/ns/restapitest/utils/tbac_token_utils.py
    pytest/ns/restapitest/utils/traversal_engine.py
    pytest/ns/restapitest/utils/utils.py
  DESTINATION usr/rift/systemtest/pytest/system/ns/restapitest/utils
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    pytest/ns/restapitest/test_inputs/test_inputs.json
  DESTINATION usr/rift/systemtest/pytest/system/ns/restapitest/test_inputs
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    pytest/ns/haproxy/test_scaling.py
  DESTINATION usr/rift/systemtest/pytest/system/ns/haproxy
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    racfg/pingpong_accounts_systest.racfg
    racfg/pingpong_vnf_systest_cloudsim.racfg
    racfg/pingpong_vnf_systest_openstack.racfg
    racfg/pingpong_scaling_systest_openstack.racfg
    racfg/pingpong_ha_systest_openstack.racfg
    racfg/pingpong_records_systest_cloudsim.racfg
    racfg/pingpong_records_systest_openstack.racfg
    racfg/pingpong_records_systest_openstack_xml.racfg
    racfg/pingpong_vnf_reload_systest_openstack.racfg
    racfg/pingpong_vnf_reload_systest_openstack_xml.racfg
    racfg/pingpong_staticip_systest_openstack.racfg
    racfg/pingpong_staticip_systest_openstack_ipv6.racfg
    racfg/pingpong_portsecurity_systest_openstack.racfg
    racfg/pingpong_port_sequencing_systest_openstack.racfg
    racfg/pingpong_port_sequencing_systest_openstack_xml.racfg
    racfg/pingpong_vnf_dependencies_systest_openstack.racfg
    racfg/pingpong_vnf_dependencies_systest_openstack_xml.racfg
    racfg/pingpong_input_params_systest.racfg
    racfg/pingpong_mro_systest.racfg
    racfg/primitives_systest.racfg
    racfg/pingpong_floating_ip.racfg
    racfg/scaling_systest.racfg
    racfg/recovery_systest.racfg
    racfg/pingpong_lp_ha_systest_openstack.racfg
    racfg/pingpong_update_descriptors_instantiate_systest_openstack.racfg
    racfg/onboard_delete_vnfs_systest_openstack.racfg
    racfg/pingpong_metadata_vdud_systest_openstack.racfg
    racfg/pingpong_multidisk_systest_openstack.racfg
    racfg/pingpong_multidisk_systest_openstack_xml.racfg
    racfg/embedded_images_vnf_multiple_accounts_systest_openstack.racfg
  DESTINATION usr/rift/systemtest/pingpong_vnf
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    racfg/l2port_chaining_systest_openstack.racfg
    racfg/metadata_vdud_systest_openstack.racfg
    racfg/ns_instantiate_memory_check.racfg
  DESTINATION usr/rift/systemtest/mano
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    racfg/gui_test_launchpad_ui.racfg
  DESTINATION usr/rift/systemtest/gui_tests
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    racfg/rbac_basics_systest.racfg
    racfg/rbac_identity.racfg
    racfg/rbac_user_roles_systest.racfg
    racfg/rbac_project_roles_systest.racfg
    racfg/rbac_account_roles_systest.racfg
    racfg/rbac_nsr_roles_systest.racfg
    racfg/rbac_onboarding_roles_systest.racfg
    racfg/rbac_syslog_server_roles_systest.racfg
    racfg/rbac_redundancy_config_roles_systest.racfg
    racfg/rbac_usage_scenarios_systest.racfg
    racfg/rbac_mano_xpaths_access.racfg
    racfg/rbac_account_roles_systest_restconf.racfg
    racfg/rbac_basics_systest_restconf.racfg
    racfg/rbac_mano_xpaths_access_restconf.racfg
    racfg/rbac_usage_scenarios_systest_restconf.racfg
    racfg/tbac_basics_systest.racfg
    racfg/tbac_identity.racfg
    racfg/tbac_token.racfg
    racfg/tbac_user_roles_systest.racfg
    racfg/tbac_project_roles_systest.racfg
    racfg/tbac_account_roles_systest.racfg
    racfg/tbac_nsr_roles_systest.racfg
    racfg/tbac_onboarding_roles_systest.racfg
    racfg/tbac_syslog_server_roles_systest.racfg
    racfg/tbac_usage_scenarios_systest.racfg
    racfg/tbac_mano_xpaths_access.racfg
    racfg/tbac_basics_systest_xml.racfg
    racfg/tbac_identity_xml.racfg
    racfg/tbac_token_xml.racfg
    racfg/tbac_user_roles_systest_xml.racfg
    racfg/tbac_project_roles_systest_xml.racfg
    racfg/tbac_account_roles_systest_xml.racfg
    racfg/tbac_nsr_roles_systest_xml.racfg
    racfg/tbac_onboarding_roles_systest_xml.racfg
    racfg/tbac_syslog_server_roles_systest_xml.racfg
    racfg/tbac_usage_scenarios_systest_xml.racfg
    racfg/tbac_mano_xpaths_access_xml.racfg
    racfg/complex_scaling.racfg
  DESTINATION usr/rift/systemtest/rbac
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    racfg/ha_basics_systest.racfg
    racfg/ha_nsr_systest.racfg
    racfg/ha_multiple_failovers_systest.racfg
  DESTINATION usr/rift/systemtest/ha
  COMPONENT ${PKG_LONG_NAME})

install(
  FILES
    racfg/multivm_vnf_slb_systest.racfg
    racfg/multivm_vnf_trafgen_systest.racfg
  DESTINATION usr/rift/systemtest/multi_vm_vnf
  COMPONENT ${INSTALL_COMPONENT}
  )
