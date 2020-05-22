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

import hashlib
import logging
import os

import psycopg2
import requests
import zmq

from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin

SDN_CONTROLLER_ADDRESS = "131.234.250.207"

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("pish-mano-sdn")
LOG.setLevel(logging.DEBUG)
logging.getLogger("manobase:messaging").setLevel(logging.INFO)

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://{}:50165".format(SDN_CONTROLLER_ADDRESS))


class SDN(ManoBasePlugin):
    """
    This class implements the SDN plugin.
    """

    def __init__(self, **kwargs):

        # call super class (will automatically connect to
        # broker and register the SDN plugin to the plugin manger)
        self.version = "0.1"
        self.description = "SDN plugin"
        self.vlan = {}

        if "db_host" in os.environ:
            self.db_host = os.environ["db_host"]
        else:
            self.db_host = "son-postgres"

        if "db_port" in os.environ:
            self.db_port = os.environ["db_port"]
        else:
            self.db_port = "5432"

        if "db_user" in os.environ:
            self.db_user = os.environ["db_user"]
        else:
            self.db_user = "sonatatest"

        if "db_password" in os.environ:
            self.db_password = os.environ["db_password"]
        else:
            self.db_password = "sonata"

        if "db_name" in os.environ:
            self.db_name = os.environ["db_name"]
        else:
            self.db_name = "vimregistry"

        LOG.info("son-plugin.SDN initializing.")
        super().__init__(version=self.version, description=self.description, **kwargs)

    def declare_subscriptions(self):
        """
        Declare topics to which we want to listen and define callback methods.
        """
        super().declare_subscriptions()

        self.manoconn.subscribe(self.on_sdn_chain_dploy, "chain.dploy.sdnplugin")
        LOG.info("son-plugin.SDN subscribing to topic chain.dploy.sdnplugin")

    def on_sdn_chain_dploy(self, message: Message):
        """
        Send IPs involved in chain to RYU controller via ZeroMQ.
        """
        LOG.info(
            "son-plugin.SDN received chain chain.dploy.sdnplugin message: %s",
            message.payload,
        )
        fg_labels = []
        ip_list = []
        payload = message.payload
        for connection_point in payload["cosd"]["forwarding_graphs"][0][
            "network_forwarding_paths"
        ][0]["connection_points"]:
            fg_labels.append(connection_point["connection_point_ref"])

        for label in fg_labels:
            if label == "input" or label == "output":
                ip = self.ip_nap_retriever(label, payload)
                if ip != "None":
                    ip_list.append(ip)
            else:
                ip_list.append(self.ip_vnf_retriever(label, payload))

        # vim_uuid = "9ead2b5a-424b-4301-94ef-9f923e09d028"

        # retrieving k8 vnf ip addtess

        # vim_ip,vim_token = self.k8_ip_token_retriever(vim_uuid)
        # service_ip = self.service_ip_retriever(vim_ip,vim_token)

        # LOG.debug("IP list {}"ip_list)

        # generate VLAN ID
        # use hashing to assign same VLAN ID for the same chain
        hash_val = hashlib.sha224(str(payload).encode("utf-8")).hexdigest()
        try:
            vlan_id = max(vlan.values()) + 1
        except:
            vlan_id = 1
        self.vlan[hash_val] = vlan_id

        forwarding_graph = [{"vlan": vlan_id}]
        for ip in range(len(ip_list)):
            forwarding_graph.append({"ip": ip_list[ip]})
        LOG.info("Service chain => {0}".format(forwarding_graph))
        socket.send_json({"forwarding_graph": forwarding_graph})
        LOG.debug("Received " + socket.recv_json()["reply"] + " event.")

    def ip_nap_retriever(self, label, message):
        try:
            if label == "input":
                return message["nap"]["ingresses"][0]["nap"]
            else:
                return message["nap"]["egresses"][0]["nap"]
        except Exception as error:
            LOG.warning("NAP IP not found! => {0}".format(error))
            return "None"

    def ip_vnf_retriever(self, label, message):
        name, nic = label.split(":")
        for vnfd in message["vnfds"]:
            if vnfd["name"] != name:
                return self.ip_cnf_retriever(name, message)
            else:
                uuid = vnfd["instance_uuid"]
                for vnfr in message["vnfrs"]:
                    if vnfr["id"] == uuid:
                        for connection_point in vnfr["virtual_deployment_units"][0][
                            "vnfc_instance"
                        ][0]["connection_points"]:
                            if connection_point["id"] == nic:
                                vnf_ip = connection_point["interface"]["address"]
                                LOG.info("{0} IP address = {1}".format(name, vnf_ip))
                                return vnf_ip

    def ip_cnf_retriever(self, name, message):
        for csd in message["csds"]:
            if csd["name"] != name:
                LOG.error("IP address not found!")
                return
            else:
                uuid = csd["instance_uuid"]
                for csr in message["csrs"]:
                    if csr["id"] == uuid:
                        service_id = "{0}-{1}".format(
                            csr["virtual_deployment_units"][0]["id"], uuid,
                        )
                        vim_uuid = csr["virtual_deployment_units"][0]["vim_id"]
                        vim_ip, vim_token = self.k8_ip_token_retriever(vim_uuid)
                        return self.service_ip_retriever(service_id, vim_ip, vim_token)

    def k8_ip_token_retriever(self, vim_uuid):

        try:
            connect_str = "dbname={0} user={1} host={2} port={3} password={4}".format(
                self.db_name, self.db_user, self.db_host, self.db_port, self.db_password
            )
            conn = psycopg2.connect(connect_str)
            cursor = conn.cursor()
            ip_query = """SELECT endpoint FROM VIM WHERE type='compute' AND uuid='{0}'""".format(
                vim_uuid
            )
            token_query = """SELECT pass FROM VIM WHERE type='compute' AND uuid='{0}'""".format(
                vim_uuid
            )
            LOG.debug("Querys have been made => {0},{1} ".format(ip_query, token_query))
            cursor.execute(ip_query)
            ip = cursor.fetchall()[0][0]
            cursor.execute(token_query)
            token = cursor.fetchall()[0][0]
            LOG.debug("Retrieved token and IP=> {0},{1}".format(token, ip))
            return (ip, token)
        except Exception as error:
            LOG.error("Token retrieval failed: {0}".format(str(error)))

    def service_ip_retriever(self, service_id, vim_ip, vim_token):

        try:
            k8_api = "https://{0}:443/api/v1/namespaces/default/services/{1}".format(
                vim_ip, service_id
            )
            header = {"Authorization": "Bearer {0}".format(vim_token)}
            response = requests.get(url=k8_api, headers=header, verify=False)
            dres = response.json()
            cn_vnf_ip = dres["status"]["loadBalancer"]["ingress"][0]["ip"]
            LOG.info("{0} ip address = {1}".format(service_id, cn_vnf_ip))
            return cn_vnf_ip
        except Exception as error:
            LOG.error("CN-VNF IP not found! =>".format(error))


def main():
    """
    Entry point to start plugin.
    :return:
    """
    LOG.info("son-plugin.SDN starting...")
    SDN()


if __name__ == "__main__":
    main()
