#!/usr/bin/python

# 
#   Copyright 2017 RIFT.IO Inc
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
import json

from ceilometerclient import client as ceclient 


class CeilometerAPIVersionException(Exception):
    def __init__(self, errors):
        self.errors = errors
        super(CeilometerAPIVersionException, self).__init__("Multiple Exception Received")
        
    def __str__(self):
        return self.__repr__()
        
    def __repr__(self):
        msg = "{} : Following Exception(s) have occured during Neutron API discovery".format(self.__class__)
        for n,e in enumerate(self.errors):
            msg += "\n"
            msg += " {}:  {}".format(n, str(e))
        return msg

class CeilometerDriver(object):
    """
    CeilometerDriver Class for image management
    """
    ### List of supported API versions in prioritized order 
    supported_versions = ["2"]
    
    def __init__(self,
                 sess_handle,
                 region_name = 'RegionOne',
                 service_type = 'metering',
                 logger = None):
        """
        Constructor for CeilometerDriver class
        Arguments:
        sess_handle (instance of class SessionDriver)
        region_name (string ): Region name
        service_type(string) : Service type name 
        logger (instance of logging.Logger)
        """

        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.ceilometer')
            logger.setLevel(logging.DEBUG)
        else:
            self.log = logger
            
        self._sess_handle = sess_handle
        #### Attempt to use API versions in prioritized order defined in
        #### CeilometerDriver.supported_versions
        def select_version(version):
            try:
                self.log.info("Attempting to use Ceilometer v%s APIs", version)
                cedrv = ceclient.Client(version=version,
                                        region_name = region_name,
                                        service_type = service_type,
                                        session=self._sess_handle.session)
            except Exception as e:
                self.log.info(str(e))
                raise
            else:
                self.log.info("Ceilometer API v%s selected", version)
                return (version, cedrv)

        errors = []
        for v in CeilometerDriver.supported_versions:
            try:
                (self._version, self._ce_drv) = select_version(v)
            except Exception as e:
                errors.append(e)
            else:
                break
        else:
            raise CeilometerAPIVersionException(errors)

    @property
    def ceilometer_endpoint(self):
        return self._ce_drv.http_client.get_endpoint()
    
    def _get_ceilometer_connection(self):
        """
        Returns instance of object ceilometerclient.client.Client
        Use for DEBUG ONLY
        """
        return self._ce_drv

    @property
    def client(self):
        """
        Returns instance of object ceilometerclient.client.Client
        Use for DEBUG ONLY
        """
        return self._ce_drv
    
    @property
    def meters(self):
        """A list of the available meters"""
        try:
            return self.client.meters.list()
        except Exception as e:
            self.log.exception("List meters operation failed. Exception: %s", str(e))
            raise
    
    @property
    def alarms(self):
        """The ceilometer client alarms manager"""
        return self.client.alarms

    def nfvi_metrics(self, vim_id):
        """Returns a dict of NFVI metrics for a given VM

        Arguments:
            vim_id - the VIM ID of the VM to retrieve the metrics for

        Returns:
            A dict of NFVI metrics

        """
        def query_latest_sample(counter_name):
            try:
                filter = json.dumps({
                    "and": [
                        {"=": {"resource": vim_id}},
                        {"=": {"counter_name": counter_name}}
                        ]
                    })
                orderby = json.dumps([{"timestamp": "DESC"}])
                result = self.client.query_samples.query(filter=filter,
                                                         orderby=orderby,
                                                         limit=1)
                return result[0]

            except IndexError:
                pass

            except Exception as e:
                self.log.exception("Got exception while querying ceilometer, exception details:%s", str(e))

            return None

        memory_usage = query_latest_sample("memory.usage")
        disk_usage = query_latest_sample("disk.usage")
        cpu_util = query_latest_sample("cpu_util")

        metrics = dict()

        if memory_usage is not None:
            memory_usage.volume = 1e6 * memory_usage.volume
            metrics["memory_usage"] = memory_usage.to_dict()

        if disk_usage is not None:
            metrics["disk_usage"] = disk_usage.to_dict()

        if cpu_util is not None:
            metrics["cpu_util"] = cpu_util.to_dict()
            # RIFT-14041 when ceilometer returns value of more than 100, make it 100
            if metrics["cpu_util"]["volume"] > 100:
                metrics["cpu_util"]["volume"] = 100

        return metrics

    def query_samples(self, vim_instance_id, counter_name, limit=1):
        """Returns a list of samples

        Arguments:
            vim_instance_id - the ID of the VIM that the samples are from
            counter_name    - the counter that the samples will come from
            limit           - a limit on the number of samples to return
                              (default: 1)

        Returns:
            A list of samples

        """
        try:
            filter = json.dumps({
                "and": [
                    {"=": {"resource": vim_instance_id}},
                    {"=": {"counter_name": counter_name}}
                    ]
                })
            try:
                result = self.client.query_samples.query(filter=filter, limit=limit)
            except Exception as e:
                self.log.exception("Query samples operation failed. Exception: %s",str(e))
            return result[-limit:]

        except Exception as e:
            self.log.exception(e)

        return []
