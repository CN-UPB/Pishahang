
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

import gi
import logging

from . import core

import xml.etree.ElementTree as etree
from gi.repository import RwTopologyYang as RwTl

gi.require_version('RwYang', '1.0')
from gi.repository import RwYang

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


logger = logging.getLogger(__name__)


class SdnSim(core.Topology):
    def __init__(self):
        super(SdnSim, self).__init__()
        self._model = RwYang.Model.create_libyang()
        self._model.load_schema_ypbc(RwTl.get_schema())

    def get_network_list(self, account):
        """
        Returns the discovered network

        @param account - a SDN account

        """

        nwtop = RwTl.YangData_IetfNetwork()
        #topology_source = "/net/boson/home1/rchamart/work/topology/l2_top.xml"
        if not account.sdnsim.has_field('topology_source') or account.sdnsim.topology_source is None:
            return nwtop
        topology_source = account.sdnsim.topology_source
        logger.info("Reading topology file: %s", topology_source)
        if 'json' in topology_source: 
            with open(topology_source,'r') as f:
                print("Reading static topology file")
                op_json = f.read()
                nwtop.from_json(self._model,op_json)
                for nw in nwtop.network:
                   nw.server_provided = False
                   logger.debug("...Network id %s", nw.network_id)
                   #nw_xpath = ("D,/nd:network[network-id={}]").format(quoted_key(nw.network_id))
                   #xact_info.respond_xpath(rwdts.XactRspCode.MORE,
                   #                 nw_xpath, nw)
        elif 'xml' in topology_source:
            tree = etree.parse(topology_source)
            root = tree.getroot()
            xmlstr = etree.tostring(root, encoding="unicode")

            # The top level topology object does not have XML conversion
            # Hence going one level down
            #l2nw1 = nwtop.network.add()
            #l2nw1.from_xml_v2(self._model, xmlstr)
            nwtop.from_xml_v2(self._model,xmlstr)

            logger.debug("Returning topology data imported from XML file")

        return nwtop
