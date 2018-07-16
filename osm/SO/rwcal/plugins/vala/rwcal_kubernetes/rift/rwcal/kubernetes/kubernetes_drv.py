#!/usr/bin/python

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

import logging

class KubernetesDriver(object):
    """
    Driver for Kubernetes
    """
    def __init__(self, logger = None, **kwargs):
        """
        Kubernetes Driver constructor
        Arguments:
           logger: (instance of logging.Logger)
           kwargs:  A dictionary of 
            {
              host (string)                           : Hostname or IP
              username (string)                       : Username
              password (string)                       : Password
              kubernetes_local_api_connector  (string): Kubnernetes Local API Connector
            }
        """

        if logger is None:
            self.log = logging.getLogger('rwcal.kubernetes.driver')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        self._host                           = kwargs['host'],
        self._username                       = kwargs['username']
        self._password                       = kwargs['password']
        self._kubernetes_local_api_connector = kwargs['kubernetes_local_api_connector']

    def create_pod():
        # kubernetes_local_api_connector calls here