"""
Copyright (c) 2015 SONATA-NFV, 2017 Pishahang
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV, Pishahang,
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

Parts of this work have been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""

import logging
import os
import time
import unittest
import uuid
from copy import copy, deepcopy
from threading import Event
from uuid import uuid4

import pytest
import yaml
from pytest_voluptuous import S
from voluptuous import Equal

from manobase.messaging import Message
from slm.slm import ServiceLifecycleManager

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("mano-plugins:slm_test")
LOG.setLevel(logging.INFO)
logging.getLogger("manobase:messaging").setLevel(logging.INFO)
logging.getLogger("manobase:plugin").setLevel(logging.INFO)

TEST_DIR = os.path.dirname(__file__)


@pytest.fixture
def corr_id():
    return str(uuid4())


@pytest.fixture
def service_id():
    return str(uuid4())


# Test the tasks that the SLM should perform in the service life cycle of the network
# services.

########################
# GENERAL
########################
@pytest.fixture
def gk_new_service_request_message():
    """
    This method helps creating messages for the service request packets.
    If it needs to be wrongly formatted, the nsd part of the request is
    removed.
    """

    descriptors_path = TEST_DIR + "/test_descriptors/"

    def load_descriptor(filename: str):
        with open(descriptors_path + filename) as descriptor_file:
            return yaml.safe_load(descriptor_file)

    # import the nsd and vnfds that form the service
    nsd_descriptor = load_descriptor("sonata-demo.yml")

    service_request = {
        "NSD": nsd_descriptor,
        "VNFD1": load_descriptor("firewall-vnfd.yml"),
        "VNFD2": load_descriptor("iperf-vnfd.yml"),
        "VNFD3": load_descriptor("tcpdump-vnfd.yml"),
    }

    return service_request


# Method that starts a timer, waiting for an event
def wait_for_event(event, timeout=5, msg="Event timed out."):
    if not event.wait(timeout):
        pytest.fail(msg=msg)


def dummy(message: Message):
    """
    Sometimes, we need a cbf for an async_call, without actually using it.
    """
    pass


#############################################################
# TEST1: test validate_deploy_request
#############################################################
def test_validate_deploy_request(
    slm: ServiceLifecycleManager, gk_new_service_request_message, corr_id
):
    """
    The method validate_deploy_request is used to check whether the
    received message that requests the deployment of a new service is
    correctly formatted.
    """

    service_id = str(uuid.uuid4())

    def validate_deploy_request(service):
        slm.set_services({service_id: service})
        slm.validate_deploy_request(service_id)
        return slm.get_services()[service_id]

    # SUBTEST1: Check a correctly formatted message
    result = validate_deploy_request(
        {"original_corr_id": corr_id, "payload": gk_new_service_request_message}
    )
    assert "INSTANTIATING" == result["status"]
    assert result["error"] is None

    # SUBTEST2: Check a message that is not a dictionary
    result = validate_deploy_request(
        {"original_corr_id": corr_id, "payload": "test message"}
    )
    assert "ERROR" == result["status"]
    assert "Request " + corr_id + ": payload is not a dict." == result["error"]

    # SUBTEST3: Check a message that contains no NSD
    message = copy(gk_new_service_request_message)
    message.pop("NSD")
    result = validate_deploy_request({"original_corr_id": corr_id, "payload": message})
    assert "ERROR" == result["status"]
    assert "Request " + corr_id + ": NSD/COSD is not a dict." == result["error"]

    # SUBTEST4: The number of VNFDs must be the same as listed in the NSD
    message = deepcopy(gk_new_service_request_message)
    message["NSD"]["network_functions"].append({})
    result = validate_deploy_request({"original_corr_id": corr_id, "payload": message})
    assert "ERROR" == result["status"]
    assert "Request " + corr_id + ": # of VNFDs doesn't match NSD." == result["error"]

    # SUBTEST5: VNFDs can not be empty
    message = deepcopy(gk_new_service_request_message)
    message["VNFD1"] = None
    result = validate_deploy_request({"original_corr_id": corr_id, "payload": message})
    assert "ERROR" == result["status"]
    assert "Request " + corr_id + ": empty VNFD." == result["error"]


###########################################################
# TEST2: Test start_next_task
###########################################################
def test_start_next_task(
    slm: ServiceLifecycleManager, gk_new_service_request_message, corr_id
):
    # Setup
    service_id = str(uuid.uuid4())
    orig_corr_id = str(uuid.uuid4())
    service_dict = {
        service_id: {
            "corr_id": corr_id,
            "original_corr_id": orig_corr_id,
            "pause_chain": True,
            "kill_chain": False,
            "schedule": ["validate_deploy_request"],
            "payload": gk_new_service_request_message,
        }
    }

    # SUBTEST1: Check if next task is correctly called

    # Run the method
    slm.set_services(service_dict)
    slm.start_next_task(service_id)
    result = slm.get_services()

    assert S({"status": "INSTANTIATING", "error": None}) <= result[service_id]

    # Setup
    service_dict = {}
    service_id = str(uuid.uuid4())
    orig_corr_id = str(uuid.uuid4())
    service_dict[service_id] = {
        "corr_id": corr_id,
        "original_corr_id": orig_corr_id,
        "pause_chain": False,
        "kill_chain": False,
        "schedule": [],
        "payload": gk_new_service_request_message,
    }

    # SUBTEST2: Check behavior if there is no next task

    # Run the method
    slm.set_services(service_dict)
    slm.start_next_task(service_id)
    result = slm.get_services()

    # Check result: if successful, service_id will not be a key in result
    assert service_id not in result


# ###############################################################
# #TEST3: Test service_instance_create
# ###############################################################
#     def test_service_instance_create(self):
#         """
#         This method tests the service_instance_create method of the SLM
#         """

#         #Setup
#         message = self.createGkNewServiceRequestMessage()
#         corr_id = str(uuid.uuid4())
#         topic = "service.instances.create"
#         prop_dict = {'reply_to': topic,
#                      'correlation_id': corr_id,
#                      'app_id': "Gatekeeper"}

#         properties = namedtuple('properties', prop_dict.keys())(*prop_dict.values())

#         schedule = self.slm_proc.service_instance_create('foo',
#                                                          'bar',
#                                                          properties,
#                                                          message)

#         #Check result: since we don't know how many of the tasks
#         #were completed by the time we got the result, we only check
#         #the final elements in the tasklist

#         #The last 7 elements from the generated result
#         generated_result = schedule[-7:]

#         #The expected last 7 elements in the list
#         expected_result = ['SLM_mapping', 'ia_prepare', 'vnf_deploy',
#                            'vnf_chain', 'wan_configure',
#                            'instruct_monitoring', 'inform_gk']

#         self.assertEqual(generated_result,
#                          expected_result,
#                          msg='lists are not equal')

###############################################################
# TEST4: Test resp_topo
###############################################################
def test_resp_topo(slm, corr_id):
    """
    This method tests the resp_topo method.
    """

    # Setup
    # Create topology message
    topology_message = [
        {
            "vim_uuid": str(uuid4()),
            "memory_used": 5,
            "memory_total": 12,
            "core_used": 4,
            "core_total": 6,
        },
        {
            "vim_uuid": str(uuid4()),
            "memory_used": 3,
            "memory_total": 5,
            "core_used": 4,
            "core_total": 5,
        },
        {
            "vim_uuid": str(uuid4()),
            "memory_used": 6,
            "memory_total": 7,
            "core_used": 2,
            "core_total": 12,
        },
    ]

    # Create ledger
    service_id = str(uuid.uuid4())
    service_dict = {
        service_id: {
            "act_corr_id": corr_id,
            "infrastructure": {"topology": None},
            "schedule": ["get_ledger"],
            "original_corr_id": corr_id,
            "pause_chain": True,
            "kill_chain": False,
        }
    }

    slm.set_services(service_dict)

    # Create Message
    topic = "infrastructure.management.compute.list"

    # Run method
    slm.resp_topo(
        Message(
            topic=topic,
            payload=topology_message,
            reply_to=topic,
            correlation_id=corr_id,
            app_id="InfrastructureAdaptor",
        )
    )

    # Check result
    result = slm.get_services()

    assert topology_message == result[service_id]["infrastructure"]["topology"]


###############################################################
# TEST5: Test resp_vnf_depl
###############################################################
@pytest.mark.parametrize("vnfs_to_resp", [1, 2])
def test_resp_vnf_depl(slm, service_id, corr_id, vnfs_to_resp):
    """
    This method tests the resp_vnf_depl method.

    Args:
        vnfs_to_resp: Number of VNFDs in the service
    """
    TOPIC = "mano.function.deploy"

    # Create the message
    with open(TEST_DIR + "/test_records/expected_vnfr_iperf.yml") as file:
        vnfr = yaml.safe_load(file)
    message = {"status": "DEPLOYED", "error": None, "vnfr": vnfr}

    # Create ledger
    slm.set_services(
        {
            service_id: {
                "act_corr_id": corr_id,
                "function": [{"id": vnfr["id"]}],
                "vnfs_to_resp": vnfs_to_resp,
                "schedule": ["get_ledger"],
                "original_corr_id": corr_id,
                "pause_chain": True,
                "kill_chain": False,
            }
        }
    )

    # Run method
    slm.resp_vnf_depl(
        Message(
            topic=TOPIC,
            reply_to=TOPIC,
            payload=message,
            correlation_id=corr_id,
            app_id="FunctionLifecycleManager",
        )
    )

    # Check result
    assert (
        S(
            {
                service_id: {
                    "function": [{"vnfr": Equal(vnfr)}],
                    "vnfs_to_resp": Equal(vnfs_to_resp - 1),
                    "schedule": ["get_ledger"],
                }
            }
        )
        <= slm.get_services()
    )


###############################################################
# TEST6: Test resp_prepare
###############################################################
def test_resp_prepare(slm, corr_id):
    """
    This method tests the resp_prepare method.
    """
    TOPIC = "infrastructure.service.prepare"

    # SUBTEST 1: Successful response message
    # Setup
    # Create the message
    message = {
        "request_status": "COMPLETED",
        "error": None,
    }

    # Create ledger
    service_id = str(uuid.uuid4())
    service_dict = {
        service_id: {
            "act_corr_id": corr_id,
            "schedule": ["get_ledger"],
            "original_corr_id": corr_id,
            "pause_chain": True,
            "current_workflow": "instantiation",
            "kill_chain": False,
        }
    }

    slm.set_services(service_dict)

    # Run method
    slm.resp_prepare(
        Message(
            topic=TOPIC,
            reply_to=TOPIC,
            payload=message,
            correlation_id=corr_id,
            app_id="InfrastructureAdaptor",
        )
    )

    # Check result
    result = slm.get_services()
    assert "status" not in result[service_id]
    assert "error" not in result[service_id]

    # #SUBTEST 2: Failed response message

    # def on_test_resp_prepare_subtest2(ch, mthd, prop, payload):

    #     message = yaml.load(payload)

    #     self.assertEqual(message['status'],
    #                      'ERROR',
    #                      msg="Status not correct in SUBTEST 1")

    #     self.assertEqual(message['error'],
    #                      'BAR',
    #                      msg="Error not correct in SUBTEST 1")

    #     self.assertTrue('timestamp' in message.keys(),
    #                      msg="Timestamp missing in SUBTEST 1")

    #     self.assertEqual(len(message.keys()),
    #                      3,
    #                     msg="Number of keys not correct in SUBTEST1")
    #     self.firstEventFinished()

    # #Setup
    # #Create the message

    # message = {'request_status': 'FOO',
    #            'message': 'BAR',
    #            }

    # payload = yaml.dump(message)

    # #Listen on feedback topic
    # self.manoconn_gk.subscribe(on_test_resp_prepare_subtest2,'service.instances.create')

    # #Create ledger
    # service_dict = {}
    # service_id = str(uuid.uuid4())
    # corr_id = str(uuid.uuid4())
    # service_dict[service_id] = {'act_corr_id':corr_id,
    #                             'schedule': ['get_ledger'],
    #                             'original_corr_id':corr_id,
    #                             'pause_chain': True,
    #                             'current_workflow': 'instantiation',
    #                             'kill_chain': False}

    # self.slm_proc.set_services(service_dict)

    # #Create properties
    # topic = "infrastructure.service.prepare"
    # prop_dict = {'reply_to': topic,
    #              'correlation_id': corr_id,
    #              'app_id': 'InfrastructureAdaptor'}

    # properties = namedtuple('props', prop_dict.keys())(*prop_dict.values())

    # #Run method
    # self.slm_proc.resp_prepare('foo', 'bar', properties, payload)

    # #Wait for the test to finish
    # self.waitForFirstEvent(timeout=5)


###############################################################
# TEST7: test contact_gk
###############################################################
@pytest.mark.parametrize("add_content", [{}, {"FOO": "BAR"}])
def test_contact_gk(slm, connection, corr_id, reraise, add_content):
    """
    This method tests the contact_gk method.
    """

    gk_message_received_event = Event()

    def on_contact_gk(message: Message):
        with reraise(catch=True):
            assert (
                S({"status": "FOO", "error": "BAR", "timestamp": float, **add_content})
                == message.payload
            )
        gk_message_received_event.set()

    # Create the ledger
    service_id = str(uuid.uuid4())
    slm.set_services(
        {
            service_id: {
                "schedule": ["get_ledger"],
                "original_corr_id": corr_id,
                "pause_chain": True,
                "status": "FOO",
                "error": "BAR",
                "kill_chain": False,
                "add_content": add_content,
                "topic": "service.instances.create",
            }
        }
    )

    # Spy the message bus
    connection.subscribe(on_contact_gk, "service.instances.create")

    # Run the method
    slm.contact_gk(service_id)

    # Wait for the test to finish
    wait_for_event(gk_message_received_event)


###############################################################
# TEST8: test request_topology
###############################################################
def test_request_topology(slm, connection, corr_id, service_id, reraise):
    """
    This method tests the request_topology method.
    """

    request_received_event = Event()

    def on_request_topology(message: Message):
        with reraise:
            assert {} == message.payload
        request_received_event.set()

    # Set the ledger
    slm.set_services(
        {
            service_id: {
                "schedule": ["get_ledger"],
                "original_corr_id": corr_id,
                "pause_chain": True,
                "kill_chain": False,
                "status": "FOO",
                "error": "BAR",
                "infrastructure": {},
            }
        }
    )

    # Spy the message bus
    connection.subscribe(on_request_topology, "infrastructure.management.compute.list")

    # Run the method
    slm.request_topology(service_id)

    # Wait for the test to finish
    wait_for_event(request_received_event)


###############################################################
# TEST9: test ia_prepare
###############################################################
# def test_ia_prepare(self):
#     """
#     This method tests the request_topology method.
#     """

#     #Check result SUBTEST 1
#     def on_ia_prepare_subtest1(ch, mthd, prop, payload):

#         message = yaml.load(payload)

#         for func in service_dict[service_id]['function']:
#             self.assertIn(func['vim_uuid'],
#                           message.keys(),
#                           msg="VIM uuid missing from keys")

#             image = func['vnfd']['virtual_deployment_units'][0]['vm_image']

#             self.assertIn(image,
#                           message[func['vim_uuid']]['vm_images'],
#                           msg="image not on correct Vim")

#         self.firstEventFinished()

#     #SUBTEST1: Check ia_prepare message if functions are mapped on
#     # different VIMs.
#     #Setup
#     #Create the ledger
#     self.wait_for_first_event.clear()
#     service_dict = {}
#     service_id = str(uuid.uuid4())
#     corr_id = str(uuid.uuid4())
#     service_dict[service_id] = {'schedule': ['get_ledger'],
#                                 'original_corr_id':corr_id,
#                                 'pause_chain': True,
#                                 'kill_chain': False,
#                                 'function': []}


#     path = '/plugins/son-mano-service-lifecycle-management/test/'

#     message = {}
#     message['instance_id'] = service_id
#     vnfd1 = open(path + 'test_descriptors/firewall-vnfd.yml', 'r')
#     vnfd2 = open(path + 'test_descriptors/iperf-vnfd.yml', 'r')
#     vnfd3 = open(path + 'test_descriptors/tcpdump-vnfd.yml', 'r')

#     service_dict[service_id]['function'].append({'vnfd': yaml.load(vnfd1)})
#     service_dict[service_id]['function'].append({'vnfd': yaml.load(vnfd2)})
#     service_dict[service_id]['function'].append({'vnfd': yaml.load(vnfd3)})

#     for vnfd in service_dict[service_id]['function']:
#         vim_uuid = str(uuid.uuid4())
#         vnfd['vim_uuid'] = vim_uuid

#     #Set the ledger
#     self.slm_proc.set_services(service_dict)

#     #Spy the message bus
#     self.manoconn_spy.subscribe(on_ia_prepare_subtest1,
#                                 'infrastructure.service.prepare')

#     #Run the method
#     self.slm_proc.ia_prepare(service_id)

#     #Wait for the test to finish
#     self.waitForFirstEvent(timeout=5)

#     #SUBTEST2: Check ia_prepare message if functions are mapped on
#     # same VIMs.
#     #Setup
#     #Create the ledger
#     self.wait_for_first_event.clear()
#     service_dict = {}
#     service_id = str(uuid.uuid4())
#     corr_id = str(uuid.uuid4())
#     service_dict[service_id] = {'schedule': ['get_ledger'],
#                                 'original_corr_id':corr_id,
#                                 'pause_chain': True,
#                                 'kill_chain': False,
#                                 'function': []}


#     path = '/plugins/son-mano-service-lifecycle-management/test/'

#     vnfd1 = open(path + 'test_descriptors/firewall-vnfd.yml', 'r')
#     vnfd2 = open(path + 'test_descriptors/iperf-vnfd.yml', 'r')
#     vnfd3 = open(path + 'test_descriptors/tcpdump-vnfd.yml', 'r')

#     service_dict[service_id]['function'].append({'vnfd': yaml.load(vnfd1)})
#     service_dict[service_id]['function'].append({'vnfd': yaml.load(vnfd2)})
#     service_dict[service_id]['function'].append({'vnfd': yaml.load(vnfd3)})

#     vim_uuid = str(uuid.uuid4())
#     for vnfd in service_dict[service_id]['function']:
#         vnfd['vim_uuid'] = vim_uuid

#     #Set the ledger
#     self.slm_proc.set_services(service_dict)

#     #Run the method
#     self.slm_proc.ia_prepare(service_id)

#     #Wait for the test to finish
#     self.waitForFirstEvent(timeout=5)

# ###############################################################
# #TEST10: test vnf_deploy
# ###############################################################
#     def test_vnf_deploy(self):
#         """
#         This method tests the request_topology method.
#         """

#         #Check result SUBTEST 1
#         def on_vnf_deploy_subtest1(ch, mthd, prop, payload):
#             message = yaml.load(payload)

#             self.assertIn(message,
#                           service_dict[service_id]['function'],
#                              msg="Payload is not correct")

#             self.vnfcounter = self.vnfcounter + 1

#             if self.vnfcounter == len(service_dict[service_id]['function']):
#                 self.firstEventFinished()

#         #SUBTEST1: Run test
#         #Setup
#         #Create the ledger
#         self.wait_for_first_event.clear()
#         service_dict = {}
#         self.vnfcounter = 0
#         service_id = str(uuid.uuid4())
#         corr_id = str(uuid.uuid4())
#         service_dict[service_id] = {'schedule': ['get_ledger'],
#                                     'original_corr_id':corr_id,
#                                     'pause_chain': True,
#                                     'kill_chain': False,
#                                     'function': []}


#         path = '/plugins/son-mano-service-lifecycle-management/test/'

#         vnfd1 = open(path + 'test_descriptors/firewall-vnfd.yml', 'r')
#         vnfd2 = open(path + 'test_descriptors/iperf-vnfd.yml', 'r')
#         vnfd3 = open(path + 'test_descriptors/tcpdump-vnfd.yml', 'r')

#         service_dict[service_id]['function'].append({'vnfd': yaml.load(vnfd1),
#                                                 'id': str(uuid.uuid4()),
#                                                 'vim_uuid': str(uuid.uuid4())})
#         service_dict[service_id]['function'].append({'vnfd': yaml.load(vnfd2),
#                                                 'id': str(uuid.uuid4()),
#                                                 'vim_uuid': str(uuid.uuid4())})
#         service_dict[service_id]['function'].append({'vnfd': yaml.load(vnfd3),
#                                                 'id': str(uuid.uuid4()),
#                                                 'vim_uuid': str(uuid.uuid4())})

#         #Set the ledger
#         self.slm_proc.set_services(service_dict)

#         #Spy the message bus
#         self.manoconn_spy.subscribe(on_vnf_deploy_subtest1,
#                                     'mano.function.deploy')

#         #Run the method
#         self.slm_proc.vnf_deploy(service_id)

#         #Wait for the test to finish
#         self.waitForFirstEvent(timeout=5)

#         #SUBTEST2: TODO: test that only one message is sent per vnf

# ###############################################################################
# #TEST11: Test build_monitoring_message
# ###############################################################################
#     def test_build_monitoring_message(self):
#         """
#         This method tests the build_monitoring_message method
#         """

#         #Setup
#         gk_request = yaml.load(self.createGkNewServiceRequestMessage())

#         #add ids to NSD and VNFDs (those used in the expected message)
#         gk_request['NSD']['uuid'] = '005606ed-be7d-4ce3-983c-847039e3a5a2'
#         gk_request['VNFD1']['uuid'] = '6a15313f-cb0a-4540-baa2-77cc6b3f5b68'
#         gk_request['VNFD2']['uuid'] = '645db4fa-a714-4cba-9617-4001477d1281'
#         gk_request['VNFD3']['uuid'] = '8a0aa837-ec1c-44e5-9907-898f6401c3ae'

#         #load nsr_file, containing both NSR and the list of VNFRs
#         message_from_ia = yaml.load(open('/plugins/son-mano-service-lifecycle-management/test/test_records/ia-nsr.yml', 'r'))
#         nsr_file = yaml.load(open('/plugins/son-mano-service-lifecycle-management/test/test_records/sonata-demo-nsr.yml', 'r'))
#         vnfrs_file = yaml.load(open('/plugins/son-mano-service-lifecycle-management/test/test_records/sonata-demo-vnfrs.yml', 'r'))

#         vnfd_firewall = gk_request['VNFD1']
#         vnfd_iperf = gk_request['VNFD2']
#         vnfd_tcpdump = gk_request['VNFD3']

#         vnfr_firewall = vnfrs_file[1]
#         vnfr_iperf = vnfrs_file[0]
#         vnfr_tcpdump = vnfrs_file[2]

#         service = {'nsd': gk_request['NSD'], 'nsr': nsr_file, 'vim_uuid': message_from_ia['instanceVimUuid']}
#         functions = []
#         functions.append({'vnfr': vnfr_iperf, 'vnfd': vnfd_iperf, 'id': vnfr_iperf['id']})
#         functions.append({'vnfr': vnfr_firewall, 'vnfd': vnfd_firewall, 'id': vnfr_firewall['id']})
#         functions.append({'vnfr': vnfr_tcpdump, 'vnfd': vnfd_tcpdump, 'id': vnfr_tcpdump['id']})

#         #Call the method
#         message = tools.build_monitoring_message(service, functions)

#         #Load expected results
#         expected_message = json.load(open('/plugins/son-mano-service-lifecycle-management/test/test_descriptors/monitoring-message.json', 'r'))

#         #Check result
#         self.assertEqual(message, expected_message, "messages are not equals")

# ###############################################################################
# #TEST12: Test build_nsr
# ###############################################################################
#     def test_build_nsr(self):
#         """
#         This method tests the build_nsr method
#         """

#         #Setup
#         gk_request = yaml.load(self.createGkNewServiceRequestMessage())
#         nsd = gk_request['NSD']

#         ia_message = yaml.load(open('/plugins/son-mano-service-lifecycle-management/test/test_records/ia-nsr.yml', 'r'))
#         expected_nsr = yaml.load(open('/plugins/son-mano-service-lifecycle-management/test/test_records/sonata-demo-nsr.yml', 'r'))

#         vnfr_ids = ['645db4fa-a714-4cba-9617-4001477d0000','6a15313f-cb0a-4540-baa2-77cc6b3f0000', '8a0aa837-ec1c-44e5-9907-898f64010000']

#         #Call method
#         message = tools.build_nsr(ia_message, nsd, vnfr_ids, ia_message['nsr']['id'])

#         #Check result
#         self.assertEqual(message, expected_nsr, "Built NSR is not equal to the expected one")

# ###############################################################################
# #TEST13: Test build_vnfr
# ###############################################################################
#     def test_build_vnfr(self):
#         """
#         This method tests the build_vnfr method
#         """

#         #Setup
#         gk_request = yaml.load(self.createGkNewServiceRequestMessage())
#         vnfd_iperf = gk_request['VNFD2']

#         ia_vnfr_iperf = yaml.load(open('/plugins/son-mano-service-lifecycle-management/test/test_records/ia-vnfr-iperf.yml', 'r'))
#         expected_vnfr_iperf = yaml.load(open('/plugins/son-mano-service-lifecycle-management/test/test_records/expected_vnfr_iperf.yml', 'r'))

#         #Call method
#         message = tools.build_vnfr(ia_vnfr_iperf['vnfr'], vnfd_iperf)

#         #Check result
#         self.assertEqual(message, expected_vnfr_iperf, "Built VNFRs are not equals to the expected ones")


if __name__ == "__main__":
    unittest.main()
