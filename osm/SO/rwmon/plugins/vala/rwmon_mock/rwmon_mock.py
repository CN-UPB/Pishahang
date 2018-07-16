
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

from gi.repository import (
    GObject,
    RwMon,
    RwTypes,
    RwmonYang as rwmon,
    )

import rw_status
import rwlogger

logger = logging.getLogger('rwmon.mock')


rwstatus = rw_status.rwstatus_from_exc_map({
    IndexError: RwTypes.RwStatus.NOTFOUND,
    KeyError: RwTypes.RwStatus.NOTFOUND,
    })


class NullImpl(object):
    def nfvi_metrics(self, account, vm_id):
        return rwmon.YangData_RwProject_Project_NfviMetrics()

    def nfvi_vcpu_metrics(self, account, vm_id):
        return rwmon.YangData_RwProject_Project_NfviMetrics_Vcpu()

    def nfvi_memory_metrics(self, account, vm_id):
        return rwmon.YangData_RwProject_Project_NfviMetrics_Memory()

    def nfvi_storage_metrics(self, account, vm_id):
        return rwmon.YangData_RwProject_Project_NfviMetrics_Storage()

    def nfvi_metrics_available(self, account):
        return True

    def alarm_create(self, account, vim_id, alarm):
        pass

    def alarm_update(self, account, alarm):
        pass

    def alarm_delete(self, account, alarm_id):
        pass

    def alarm_list(self, account):
        return list()


class MockMonitoringPlugin(GObject.Object, RwMon.Monitoring):
    def __init__(self):
        GObject.Object.__init__(self)
        self._impl = NullImpl()

    @rwstatus
    def do_init(self, rwlog_ctx):
        if not any(isinstance(h, rwlogger.RwLogger) for h in logger.handlers):
            logger.addHandler(
                rwlogger.RwLogger(
                    category="rw-monitor-log",
                    subcategory="mock",
                    log_hdl=rwlog_ctx,
                )
            )

    @rwstatus
    def do_nfvi_metrics(self, account, vm_id):
        return self._impl.nfvi_metrics(account, vm_id)

    @rwstatus
    def do_nfvi_vcpu_metrics(self, account, vm_id):
        return self._impl.nfvi_vcpu_metrics(account, vm_id)

    @rwstatus
    def do_nfvi_memory_metrics(self, account, vm_id):
        return self._impl.nfvi_memory_metrics(account, vm_id)

    @rwstatus
    def do_nfvi_storage_metrics(self, account, vm_id):
        return self._impl.nfvi_storage_metrics(account, vm_id)

    @rwstatus
    def do_nfvi_metrics_available(self, account):
        return self._impl.nfvi_metrics_available(account)

    @rwstatus(ret_on_failure=[None])
    def do_alarm_create(self, account, vim_id, alarm):
        return self._impl.alarm_create(account, vim_id, alarm)

    @rwstatus(ret_on_failure=[None])
    def do_alarm_update(self, account, alarm):
        return self._impl.alarm_update(account, alarm)

    @rwstatus(ret_on_failure=[None])
    def do_alarm_delete(self, account, alarm_id):
        return self._impl.alarm_delete(account, alarm_id)

    @rwstatus(ret_on_failure=[None])
    def do_alarm_list(self, account):
        return self._impl.alarm_list(account)

    def set_impl(self, impl):
        self._impl = impl
