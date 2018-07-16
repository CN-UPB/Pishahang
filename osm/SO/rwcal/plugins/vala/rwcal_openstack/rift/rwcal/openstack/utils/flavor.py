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

import re
import gi

gi.require_version('RwcalYang', '1.0')
from gi.repository import RwcalYang


class GuestEPAUtils(object):
    """
    Utility class for Host EPA to Openstack flavor extra_specs conversion routines
    """
    def __init__(self):
        self._mano_to_espec_cpu_pinning_policy = {
            'DEDICATED' : 'dedicated',
            'SHARED'    : 'shared',
            'ANY'       : 'any',
        }

        self._espec_to_mano_cpu_pinning_policy = {
            'dedicated' : 'DEDICATED',
            'shared'    : 'SHARED',
            'any'       : 'ANY',
        }
        
        self._mano_to_espec_mempage_size = {
            'LARGE'        : 'large', 
            'SMALL'        : 'small',
            'SIZE_2MB'     :  2048,
            'SIZE_1GB'     :  1048576,
            'PREFER_LARGE' : 'large',
        }

        self._espec_to_mano_mempage_size = {
            'large'        : 'LARGE', 
            'small'        : 'SMALL',
             2048          : 'SIZE_2MB',
             1048576       : 'SIZE_1GB',
            'large'        : 'PREFER_LARGE',
        }

        self._mano_to_espec_cpu_thread_pinning_policy = {
            'AVOID'    : 'avoid',
            'SEPARATE' : 'separate',
            'ISOLATE'  : 'isolate',
            'PREFER'   : 'prefer',
        }

        self._espec_to_mano_cpu_thread_pinning_policy = {
            'avoid'    : 'AVOID',
            'separate' : 'SEPARATE',
            'isolate'  : 'ISOLATE',
            'prefer'   : 'PREFER',
        }

        self._espec_to_mano_numa_memory_policy = {
            'strict'   : 'STRICT',
            'preferred': 'PREFERRED'
        }

        self._mano_to_espec_numa_memory_policy = {
            'STRICT'   : 'strict',
            'PREFERRED': 'preferred'
        }

    def mano_to_extra_spec_cpu_pinning_policy(self, cpu_pinning_policy):
        if cpu_pinning_policy in self._mano_to_espec_cpu_pinning_policy:
            return self._mano_to_espec_cpu_pinning_policy[cpu_pinning_policy]
        else:
            return None

    def extra_spec_to_mano_cpu_pinning_policy(self, cpu_pinning_policy):
        if cpu_pinning_policy in self._espec_to_mano_cpu_pinning_policy:
            return self._espec_to_mano_cpu_pinning_policy[cpu_pinning_policy]
        else:
            return None

    def mano_to_extra_spec_mempage_size(self, mempage_size):
        if mempage_size in self._mano_to_espec_mempage_size:
            return self._mano_to_espec_mempage_size[mempage_size]
        else:
            return None
        
    def extra_spec_to_mano_mempage_size(self, mempage_size):
        if mempage_size in self._espec_to_mano_mempage_size:
            return self._espec_to_mano_mempage_size[mempage_size]
        else:
            return None

    def mano_to_extra_spec_cpu_thread_pinning_policy(self, cpu_thread_pinning_policy):
        if cpu_thread_pinning_policy in self._mano_to_espec_cpu_thread_pinning_policy:
            return self._mano_to_espec_cpu_thread_pinning_policy[cpu_thread_pinning_policy]
        else:
            return None

    def extra_spec_to_mano_cpu_thread_pinning_policy(self, cpu_thread_pinning_policy):
        if cpu_thread_pinning_policy in self._espec_to_mano_cpu_thread_pinning_policy:
            return self._espec_to_mano_cpu_thread_pinning_policy[cpu_thread_pinning_policy]
        else:
            return None

    def mano_to_extra_spec_trusted_execution(self, trusted_execution):
        if trusted_execution:
            return 'trusted'
        else:
            return 'untrusted'

    def extra_spec_to_mano_trusted_execution(self, trusted_execution):
        if trusted_execution == 'trusted':
            return True
        elif trusted_execution == 'untrusted':
            return False
        else:
            return None
        
    def mano_to_extra_spec_numa_node_count(self, numa_node_count):
        return numa_node_count

    def extra_specs_to_mano_numa_node_count(self, numa_node_count):
        return int(numa_node_count)
    
    def mano_to_extra_spec_numa_memory_policy(self, numa_memory_policy):
        if numa_memory_policy in self._mano_to_espec_numa_memory_policy:
            return self._mano_to_espec_numa_memory_policy[numa_memory_policy]
        else:
            return None

    def extra_to_mano_spec_numa_memory_policy(self, numa_memory_policy):
        if numa_memory_policy in self._espec_to_mano_numa_memory_policy:
            return self._espec_to_mano_numa_memory_policy[numa_memory_policy]
        else:
            return None
        
                                                          
    
    
class HostEPAUtils(object):
    """
    Utility class for Host EPA to Openstack flavor extra_specs conversion routines
    """
    def __init__(self):
        self._mano_to_espec_cpumodel = {
            "PREFER_WESTMERE"     : "Westmere",
            "REQUIRE_WESTMERE"    : "Westmere",
            "PREFER_SANDYBRIDGE"  : "SandyBridge",
            "REQUIRE_SANDYBRIDGE" : "SandyBridge",
            "PREFER_IVYBRIDGE"    : "IvyBridge",
            "REQUIRE_IVYBRIDGE"   : "IvyBridge",
            "PREFER_HASWELL"      : "Haswell",
            "REQUIRE_HASWELL"     : "Haswell",
            "PREFER_BROADWELL"    : "Broadwell",
            "REQUIRE_BROADWELL"   : "Broadwell",
            "PREFER_NEHALEM"      : "Nehalem",
            "REQUIRE_NEHALEM"     : "Nehalem",
            "PREFER_PENRYN"       : "Penryn",
            "REQUIRE_PENRYN"      : "Penryn",
            "PREFER_CONROE"       : "Conroe",
            "REQUIRE_CONROE"      : "Conroe",
            "PREFER_CORE2DUO"     : "Core2Duo",
            "REQUIRE_CORE2DUO"    : "Core2Duo",
        }

        self._espec_to_mano_cpumodel = {
            "Westmere"     : "REQUIRE_WESTMERE",
            "SandyBridge"  : "REQUIRE_SANDYBRIDGE",
            "IvyBridge"    : "REQUIRE_IVYBRIDGE",
            "Haswell"      : "REQUIRE_HASWELL",
            "Broadwell"    : "REQUIRE_BROADWELL",
            "Nehalem"      : "REQUIRE_NEHALEM",
            "Penryn"       : "REQUIRE_PENRYN",
            "Conroe"       : "REQUIRE_CONROE",
            "Core2Duo"     : "REQUIRE_CORE2DUO",
        }

        self._mano_to_espec_cpuarch = {
            "PREFER_X86"     : "x86",
            "REQUIRE_X86"    : "x86",
            "PREFER_X86_64"  : "x86_64",
            "REQUIRE_X86_64" : "x86_64",
            "PREFER_I686"    : "i686",
            "REQUIRE_I686"   : "i686",
            "PREFER_IA64"    : "ia64",
            "REQUIRE_IA64"   : "ia64",
            "PREFER_ARMV7"   : "ARMv7",
            "REQUIRE_ARMV7"  : "ARMv7",
            "PREFER_ARMV8"   : "ARMv8-A",
            "REQUIRE_ARMV8"  : "ARMv8-A",
        }

        self._espec_to_mano_cpuarch = {
            "x86"     : "REQUIRE_X86",
            "x86_64"  : "REQUIRE_X86_64",
            "i686"    : "REQUIRE_I686",
            "ia64"    : "REQUIRE_IA64",
            "ARMv7-A" : "REQUIRE_ARMV7",
            "ARMv8-A" : "REQUIRE_ARMV8",
        }

        self._mano_to_espec_cpuvendor = {
            "PREFER_INTEL"  : "Intel",
            "REQUIRE_INTEL" : "Intel",
            "PREFER_AMD"    : "AMD",
            "REQUIRE_AMD"   : "AMD",
        }

        self._espec_to_mano_cpuvendor = {
            "Intel" : "REQUIRE_INTEL",
            "AMD"   : "REQUIRE_AMD",
        }

        self._mano_to_espec_cpufeatures = {
            "PREFER_AES"       : "aes",
            "REQUIRE_AES"      : "aes",
            "REQUIRE_VME"      : "vme",
            "PREFER_VME"       : "vme",
            "REQUIRE_DE"       : "de",
            "PREFER_DE"        : "de",
            "REQUIRE_PSE"      : "pse",
            "PREFER_PSE"       : "pse",
            "REQUIRE_TSC"      : "tsc",
            "PREFER_TSC"       : "tsc",
            "REQUIRE_MSR"      : "msr",
            "PREFER_MSR"       : "msr",
            "REQUIRE_PAE"      : "pae",
            "PREFER_PAE"       : "pae",
            "REQUIRE_MCE"      : "mce",
            "PREFER_MCE"       : "mce",
            "REQUIRE_CX8"      : "cx8",
            "PREFER_CX8"       : "cx8",
            "REQUIRE_APIC"     : "apic",
            "PREFER_APIC"      : "apic",
            "REQUIRE_SEP"      : "sep",
            "PREFER_SEP"       : "sep",
            "REQUIRE_MTRR"     : "mtrr",
            "PREFER_MTRR"      : "mtrr",
            "REQUIRE_PGE"      : "pge",
            "PREFER_PGE"       : "pge",
            "REQUIRE_MCA"      : "mca",
            "PREFER_MCA"       : "mca",
            "REQUIRE_CMOV"     : "cmov",
            "PREFER_CMOV"      : "cmov",
            "REQUIRE_PAT"      : "pat",
            "PREFER_PAT"       : "pat",
            "REQUIRE_PSE36"    : "pse36",
            "PREFER_PSE36"     : "pse36",
            "REQUIRE_CLFLUSH"  : "clflush",
            "PREFER_CLFLUSH"   : "clflush",
            "REQUIRE_DTS"      : "dts",
            "PREFER_DTS"       : "dts",
            "REQUIRE_ACPI"     : "acpi",
            "PREFER_ACPI"      : "acpi",
            "REQUIRE_MMX"      : "mmx",
            "PREFER_MMX"       : "mmx",
            "REQUIRE_FXSR"     : "fxsr",
            "PREFER_FXSR"      : "fxsr",
            "REQUIRE_SSE"      : "sse",
            "PREFER_SSE"       : "sse",
            "REQUIRE_SSE2"     : "sse2",
            "PREFER_SSE2"      : "sse2",
            "REQUIRE_SS"       : "ss",
            "PREFER_SS"        : "ss",
            "REQUIRE_HT"       : "ht",
            "PREFER_HT"        : "ht",
            "REQUIRE_TM"       : "tm",
            "PREFER_TM"        : "tm",
            "REQUIRE_IA64"     : "ia64",
            "PREFER_IA64"      : "ia64",
            "REQUIRE_PBE"      : "pbe",
            "PREFER_PBE"       : "pbe",
            "REQUIRE_RDTSCP"   : "rdtscp",
            "PREFER_RDTSCP"    : "rdtscp",
            "REQUIRE_PNI"      : "pni",
            "PREFER_PNI"       : "pni",
            "REQUIRE_PCLMULQDQ": "pclmulqdq",
            "PREFER_PCLMULQDQ" : "pclmulqdq",
            "REQUIRE_DTES64"   : "dtes64",
            "PREFER_DTES64"    : "dtes64",
            "REQUIRE_MONITOR"  : "monitor",
            "PREFER_MONITOR"   : "monitor",
            "REQUIRE_DS_CPL"   : "ds_cpl",
            "PREFER_DS_CPL"    : "ds_cpl",
            "REQUIRE_VMX"      : "vmx",
            "PREFER_VMX"       : "vmx",
            "REQUIRE_SMX"      : "smx",
            "PREFER_SMX"       : "smx",
            "REQUIRE_EST"      : "est",
            "PREFER_EST"       : "est",
            "REQUIRE_TM2"      : "tm2",
            "PREFER_TM2"       : "tm2",
            "REQUIRE_SSSE3"    : "ssse3",
            "PREFER_SSSE3"     : "ssse3",
            "REQUIRE_CID"      : "cid",
            "PREFER_CID"       : "cid",
            "REQUIRE_FMA"      : "fma",
            "PREFER_FMA"       : "fma",
            "REQUIRE_CX16"     : "cx16",
            "PREFER_CX16"      : "cx16",
            "REQUIRE_XTPR"     : "xtpr",
            "PREFER_XTPR"      : "xtpr",
            "REQUIRE_PDCM"     : "pdcm",
            "PREFER_PDCM"      : "pdcm",
            "REQUIRE_PCID"     : "pcid",
            "PREFER_PCID"      : "pcid",
            "REQUIRE_DCA"      : "dca",
            "PREFER_DCA"       : "dca",
            "REQUIRE_SSE4_1"   : "sse4_1",
            "PREFER_SSE4_1"    : "sse4_1",
            "REQUIRE_SSE4_2"   : "sse4_2",
            "PREFER_SSE4_2"    : "sse4_2",
            "REQUIRE_X2APIC"   : "x2apic",
            "PREFER_X2APIC"    : "x2apic",
            "REQUIRE_MOVBE"    : "movbe",
            "PREFER_MOVBE"     : "movbe",
            "REQUIRE_POPCNT"   : "popcnt",
            "PREFER_POPCNT"    : "popcnt",
            "REQUIRE_TSC_DEADLINE_TIMER"   : "tsc_deadline_timer",
            "PREFER_TSC_DEADLINE_TIMER"    : "tsc_deadline_timer",
            "REQUIRE_XSAVE"    : "xsave",
            "PREFER_XSAVE"     : "xsave",
            "REQUIRE_AVX"      : "avx",
            "PREFER_AVX"       : "avx",
            "REQUIRE_F16C"     : "f16c",
            "PREFER_F16C"      : "f16c",
            "REQUIRE_RDRAND"   : "rdrand",
            "PREFER_RDRAND"    : "rdrand",
            "REQUIRE_FSGSBASE" : "fsgsbase",
            "PREFER_FSGSBASE"  : "fsgsbase",
            "REQUIRE_BMI1"     : "bmi1",
            "PREFER_BMI1"      : "bmi1",
            "REQUIRE_HLE"      : "hle",
            "PREFER_HLE"       : "hle",
            "REQUIRE_AVX2"     : "avx2",
            "PREFER_AVX2"      : "avx2",
            "REQUIRE_SMEP"     : "smep",
            "PREFER_SMEP"      : "smep",
            "REQUIRE_BMI2"     : "bmi2",
            "PREFER_BMI2"      : "bmi2",
            "REQUIRE_ERMS"     : "erms",
            "PREFER_ERMS"      : "erms",
            "REQUIRE_INVPCID"  : "invpcid",
            "PREFER_INVPCID"   : "invpcid",
            "REQUIRE_RTM"      : "rtm",
            "PREFER_RTM"       : "rtm",
            "REQUIRE_MPX"      : "mpx",
            "PREFER_MPX"       : "mpx",
            "REQUIRE_RDSEED"   : "rdseed",
            "PREFER_RDSEED"    : "rdseed",
            "REQUIRE_ADX"      : "adx",
            "PREFER_ADX"       : "adx",
            "REQUIRE_SMAP"     : "smap",
            "PREFER_SMAP"      : "smap",
        }

        self._espec_to_mano_cpufeatures = {
            "aes"      : "REQUIRE_AES",
            "vme"      : "REQUIRE_VME",
            "de"       : "REQUIRE_DE",
            "pse"      : "REQUIRE_PSE",
            "tsc"      : "REQUIRE_TSC",
            "msr"      : "REQUIRE_MSR",
            "pae"      : "REQUIRE_PAE",
            "mce"      : "REQUIRE_MCE",
            "cx8"      : "REQUIRE_CX8",
            "apic"     : "REQUIRE_APIC",
            "sep"      : "REQUIRE_SEP",
            "mtrr"     : "REQUIRE_MTRR",
            "pge"      : "REQUIRE_PGE",
            "mca"      : "REQUIRE_MCA",
            "cmov"     : "REQUIRE_CMOV",
            "pat"      : "REQUIRE_PAT",
            "pse36"    : "REQUIRE_PSE36",
            "clflush"  : "REQUIRE_CLFLUSH",
            "dts"      : "REQUIRE_DTS",
            "acpi"     : "REQUIRE_ACPI",
            "mmx"      : "REQUIRE_MMX",
            "fxsr"     : "REQUIRE_FXSR",
            "sse"      : "REQUIRE_SSE",
            "sse2"     : "REQUIRE_SSE2",
            "ss"       : "REQUIRE_SS",
            "ht"       : "REQUIRE_HT",
            "tm"       : "REQUIRE_TM",
            "ia64"     : "REQUIRE_IA64",
            "pbe"      : "REQUIRE_PBE",
            "rdtscp"   : "REQUIRE_RDTSCP",
            "pni"      : "REQUIRE_PNI",
            "pclmulqdq": "REQUIRE_PCLMULQDQ",
            "dtes64"   : "REQUIRE_DTES64",
            "monitor"  : "REQUIRE_MONITOR",
            "ds_cpl"   : "REQUIRE_DS_CPL",
            "vmx"      : "REQUIRE_VMX",
            "smx"      : "REQUIRE_SMX",
            "est"      : "REQUIRE_EST",
            "tm2"      : "REQUIRE_TM2",
            "ssse3"    : "REQUIRE_SSSE3",
            "cid"      : "REQUIRE_CID",
            "fma"      : "REQUIRE_FMA",
            "cx16"     : "REQUIRE_CX16",
            "xtpr"     : "REQUIRE_XTPR",
            "pdcm"     : "REQUIRE_PDCM",
            "pcid"     : "REQUIRE_PCID",
            "dca"      : "REQUIRE_DCA",
            "sse4_1"   : "REQUIRE_SSE4_1",
            "sse4_2"   : "REQUIRE_SSE4_2",
            "x2apic"   : "REQUIRE_X2APIC",
            "movbe"    : "REQUIRE_MOVBE",
            "popcnt"   : "REQUIRE_POPCNT",
            "tsc_deadline_timer"   : "REQUIRE_TSC_DEADLINE_TIMER",
            "xsave"    : "REQUIRE_XSAVE",
            "avx"      : "REQUIRE_AVX",
            "f16c"     : "REQUIRE_F16C",
            "rdrand"   : "REQUIRE_RDRAND",
            "fsgsbase" : "REQUIRE_FSGSBASE",
            "bmi1"     : "REQUIRE_BMI1",
            "hle"      : "REQUIRE_HLE",
            "avx2"     : "REQUIRE_AVX2",
            "smep"     : "REQUIRE_SMEP",
            "bmi2"     : "REQUIRE_BMI2",
            "erms"     : "REQUIRE_ERMS",
            "invpcid"  : "REQUIRE_INVPCID",
            "rtm"      : "REQUIRE_RTM",
            "mpx"      : "REQUIRE_MPX",
            "rdseed"   : "REQUIRE_RDSEED",
            "adx"      : "REQUIRE_ADX",
            "smap"     : "REQUIRE_SMAP",
        }

    def mano_to_extra_spec_cpu_model(self, cpu_model):
        if cpu_model in self._mano_to_espec_cpumodel:
            return self._mano_to_espec_cpumodel[cpu_model]
        else:
            return None
            
    def extra_specs_to_mano_cpu_model(self, cpu_model):
        if cpu_model in self._espec_to_mano_cpumodel:
            return self._espec_to_mano_cpumodel[cpu_model]
        else:
            return None
        
    def mano_to_extra_spec_cpu_arch(self, cpu_arch):
        if cpu_arch in self._mano_to_espec_cpuarch:
            return self._mano_to_espec_cpuarch[cpu_arch]
        else:
            return None
        
    def extra_specs_to_mano_cpu_arch(self, cpu_arch):
        if cpu_arch in self._espec_to_mano_cpuarch:
            return self._espec_to_mano_cpuarch[cpu_arch]
        else:
            return None
    
    def mano_to_extra_spec_cpu_vendor(self, cpu_vendor):
        if cpu_vendor in self._mano_to_espec_cpuvendor:
            return self._mano_to_espec_cpuvendor[cpu_vendor]
        else:
            return None

    def extra_spec_to_mano_cpu_vendor(self, cpu_vendor):
        if cpu_vendor in self._espec_to_mano_cpuvendor:
            return self._espec_to_mano_cpuvendor[cpu_vendor]
        else:
            return None
    
    def mano_to_extra_spec_cpu_socket_count(self, cpu_sockets):
        return cpu_sockets

    def extra_spec_to_mano_cpu_socket_count(self, cpu_sockets):
        return int(cpu_sockets)
    
    def mano_to_extra_spec_cpu_core_count(self, cpu_core_count):
        return cpu_core_count

    def extra_spec_to_mano_cpu_core_count(self, cpu_core_count):
        return int(cpu_core_count)
    
    def mano_to_extra_spec_cpu_core_thread_count(self, core_thread_count):
        return core_thread_count

    def extra_spec_to_mano_cpu_core_thread_count(self, core_thread_count):
        return int(core_thread_count)

    def mano_to_extra_spec_cpu_features(self, features):
        cpu_features = []
        epa_feature_str = None
        for f in features:
            if f in self._mano_to_espec_cpufeatures:
                cpu_features.append(self._mano_to_espec_cpufeatures[f])
                
        if len(cpu_features) > 1:
            epa_feature_str =  '<all-in> '+ " ".join(cpu_features)
        elif len(cpu_features) == 1:
            epa_feature_str = " ".join(cpu_features)

        return epa_feature_str

    def extra_spec_to_mano_cpu_features(self, features):
        oper_symbols = ['=', '<in>', '<all-in>', '==', '!=', '>=', '<=', 's==', 's!=', 's<', 's<=', 's>', 's>=']
        cpu_features = []
        result = None
        for oper in oper_symbols:
            regex = '^'+oper+' (.*?)$'
            result = re.search(regex, features)
            if result is not None:
                break
            
        if result is not None:
            feature_list = result.group(1)
        else:
            feature_list = features

        for f in feature_list.split():
            if f in self._espec_to_mano_cpufeatures:
                cpu_features.append(self._espec_to_mano_cpufeatures[f])

        return cpu_features
    

class ExtraSpecUtils(object):
    """
    General utility class for flavor Extra Specs processing
    """
    def __init__(self):
        self.host = HostEPAUtils()
        self.guest = GuestEPAUtils()
        self.extra_specs_keywords = [ 'hw:cpu_policy',
                                      'hw:cpu_threads_policy',
                                      'hw:mem_page_size',
                                      'hw:numa_nodes',
                                      'hw:numa_mempolicy',
                                      'hw:numa_cpus',
                                      'hw:numa_mem',
                                      'trust:trusted_host',
                                      'pci_passthrough:alias',
                                      'capabilities:cpu_info:model',
                                      'capabilities:cpu_info:arch',
                                      'capabilities:cpu_info:vendor',
                                      'capabilities:cpu_info:topology:sockets',
                                      'capabilities:cpu_info:topology:cores',
                                      'capabilities:cpu_info:topology:threads',
                                      'capabilities:cpu_info:features',
                                ]
        self.extra_specs_regex = re.compile("^"+"|^".join(self.extra_specs_keywords))



class FlavorUtils(object):
    """
    Utility class for handling the flavor 
    """
    def __init__(self, driver):
        """
        Constructor for class
        Arguments:
          driver: object of OpenstackDriver()
        """
        self._epa = ExtraSpecUtils()
        self._driver = driver
        self.log = driver.log
        
    @property
    def driver(self):
        return self._driver
    
    def _get_guest_epa_specs(self, guest_epa):
        """
        Returns EPA Specs dictionary for guest_epa attributes
        """
        epa_specs = dict()
        if guest_epa.has_field('mempage_size'):
            mempage_size = self._epa.guest.mano_to_extra_spec_mempage_size(guest_epa.mempage_size)
            if mempage_size is not None:
                epa_specs['hw:mem_page_size'] = mempage_size

        if guest_epa.has_field('cpu_pinning_policy'):
            cpu_pinning_policy = self._epa.guest.mano_to_extra_spec_cpu_pinning_policy(guest_epa.cpu_pinning_policy)
            if cpu_pinning_policy is not None:
                epa_specs['hw:cpu_policy'] = cpu_pinning_policy

        if guest_epa.has_field('cpu_thread_pinning_policy'):
            cpu_thread_pinning_policy = self._epa.guest.mano_to_extra_spec_cpu_thread_pinning_policy(guest_epa.cpu_thread_pinning_policy)
            if cpu_thread_pinning_policy is None:
                epa_specs['hw:cpu_threads_policy'] = cpu_thread_pinning_policy

        if guest_epa.has_field('trusted_execution'):
            trusted_execution = self._epa.guest.mano_to_extra_spec_trusted_execution(guest_epa.trusted_execution)
            if trusted_execution is not None:
                epa_specs['trust:trusted_host'] = trusted_execution

        if guest_epa.has_field('numa_node_policy'):
            if guest_epa.numa_node_policy.has_field('node_cnt'):
                numa_node_count = self._epa.guest.mano_to_extra_spec_numa_node_count(guest_epa.numa_node_policy.node_cnt)
                if numa_node_count is not None:
                    epa_specs['hw:numa_nodes'] = numa_node_count

            if guest_epa.numa_node_policy.has_field('mem_policy'):
                numa_memory_policy = self._epa.guest.mano_to_extra_spec_numa_memory_policy(guest_epa.numa_node_policy.mem_policy)
                if numa_memory_policy is not None:
                    epa_specs['hw:numa_mempolicy'] = numa_memory_policy

            if guest_epa.numa_node_policy.has_field('node'):
                for node in guest_epa.numa_node_policy.node:
                    if node.has_field('vcpu') and node.vcpu:
                        epa_specs['hw:numa_cpus.'+str(node.id)] = ','.join([str(j.id) for j in node.vcpu])
                    if node.memory_mb:
                        epa_specs['hw:numa_mem.'+str(node.id)] = str(node.memory_mb)

        if guest_epa.has_field('pcie_device'):
            pci_devices = []
            for device in guest_epa.pcie_device:
                pci_devices.append(device.device_id +':'+str(device.count))
            epa_specs['pci_passthrough:alias'] = ','.join(pci_devices)

        return epa_specs

    def _get_host_epa_specs(self,host_epa):
        """
        Returns EPA Specs dictionary for host_epa attributes
        """
        epa_specs = dict()

        if host_epa.has_field('cpu_model'):
            cpu_model = self._epa.host.mano_to_extra_spec_cpu_model(host_epa.cpu_model)
            if cpu_model is not None:
                epa_specs['capabilities:cpu_info:model'] = cpu_model

        if host_epa.has_field('cpu_arch'):
            cpu_arch = self._epa.host.mano_to_extra_spec_cpu_arch(host_epa.cpu_arch)
            if cpu_arch is not None:
                epa_specs['capabilities:cpu_info:arch'] = cpu_arch

        if host_epa.has_field('cpu_vendor'):
            cpu_vendor = self._epa.host.mano_to_extra_spec_cpu_vendor(host_epa.cpu_vendor)
            if cpu_vendor is not None:
                epa_specs['capabilities:cpu_info:vendor'] = cpu_vendor

        if host_epa.has_field('cpu_socket_count'):
            cpu_socket_count = self._epa.host.mano_to_extra_spec_cpu_socket_count(host_epa.cpu_socket_count)
            if cpu_socket_count is not None:
                epa_specs['capabilities:cpu_info:topology:sockets'] = cpu_socket_count

        if host_epa.has_field('cpu_core_count'):
            cpu_core_count = self._epa.host.mano_to_extra_spec_cpu_core_count(host_epa.cpu_core_count)
            if cpu_core_count is not None:
                epa_specs['capabilities:cpu_info:topology:cores'] = cpu_core_count

        if host_epa.has_field('cpu_core_thread_count'):
            cpu_core_thread_count = self._epa.host.mano_to_extra_spec_cpu_core_thread_count(host_epa.cpu_core_thread_count)
            if cpu_core_thread_count is not None:
                epa_specs['capabilities:cpu_info:topology:threads'] = cpu_core_thread_count

        if host_epa.has_field('cpu_feature'):
            cpu_features = []
            espec_cpu_features = []
            for feature in host_epa.cpu_feature:
                cpu_features.append(feature.feature)
            espec_cpu_features = self._epa.host.mano_to_extra_spec_cpu_features(cpu_features)
            if espec_cpu_features is not None:
                epa_specs['capabilities:cpu_info:features'] = espec_cpu_features
        return epa_specs

    def _get_hypervisor_epa_specs(self,guest_epa):
        """
        Returns EPA Specs dictionary for hypervisor_epa attributes
        """
        hypervisor_epa = dict()
        return hypervisor_epa

    def _get_vswitch_epa_specs(self, guest_epa):
        """
        Returns EPA Specs dictionary for vswitch_epa attributes
        """
        vswitch_epa = dict()
        return vswitch_epa

    def _get_host_aggregate_epa_specs(self, host_aggregate):
        """
        Returns EPA Specs dictionary for host aggregates
        """
        epa_specs = dict()
        for aggregate in host_aggregate:
            epa_specs['aggregate_instance_extra_specs:'+aggregate.metadata_key] = aggregate.metadata_value

        return epa_specs
    
    def get_extra_specs(self, flavor):
        """
        Returns epa_specs dictionary based on flavor information
        Arguments
           flavor -- Protobuf GI object for flavor_info (RwcalYang.FlavorInfoItem())
        Returns:
           A dictionary of extra_specs in format understood by novaclient library
        """
        epa_specs = dict()
        if flavor.has_field('guest_epa'):
            guest_epa = self._get_guest_epa_specs(flavor.guest_epa)
            epa_specs.update(guest_epa)
        if flavor.has_field('host_epa'):
            host_epa = self._get_host_epa_specs(flavor.host_epa)
            epa_specs.update(host_epa)
        if flavor.has_field('hypervisor_epa'):
            hypervisor_epa = self._get_hypervisor_epa_specs(flavor.hypervisor_epa)
            epa_specs.update(hypervisor_epa)
        if flavor.has_field('vswitch_epa'):
            vswitch_epa = self._get_vswitch_epa_specs(flavor.vswitch_epa)
            epa_specs.update(vswitch_epa)
        if flavor.has_field('host_aggregate'):
            host_aggregate = self._get_host_aggregate_epa_specs(flavor.host_aggregate)
            epa_specs.update(host_aggregate)
        return epa_specs


    def parse_vm_flavor_epa_info(self, flavor_info):
        """
        Parse the flavor_info dictionary (returned by python-client) for vm_flavor

        Arguments:
           flavor_info: A dictionary object return by novaclient library listing flavor attributes

        Returns:
               vm_flavor = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList_VmFlavor()
        """
        vm_flavor = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList_VmFlavor()

        if 'vcpus' in flavor_info and flavor_info['vcpus']:
            vm_flavor.vcpu_count = flavor_info['vcpus']

        if 'ram' in flavor_info and flavor_info['ram']:
            vm_flavor.memory_mb  = flavor_info['ram']

        if 'disk' in flavor_info and flavor_info['disk']:
            vm_flavor.storage_gb  = flavor_info['disk']

        return vm_flavor
    
    def parse_guest_epa_info(self, flavor_info):
        """
        Parse the flavor_info dictionary (returned by python-client) for guest_epa

        Arguments:
           flavor_info: A dictionary object return by novaclient library listing flavor attributes

        Returns:
           guest_epa = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList_GuestEpa()
        """
        guest_epa = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList_GuestEpa()
        if 'extra_specs' not in flavor_info or flavor_info['extra_specs'] is None:
            return guest_epa
        for attr in flavor_info['extra_specs']:
            if attr == 'hw:cpu_policy':
                cpu_pinning_policy = self._epa.guest.extra_spec_to_mano_cpu_pinning_policy(flavor_info['extra_specs']['hw:cpu_policy'])
                if cpu_pinning_policy is not None:
                    guest_epa.cpu_pinning_policy = cpu_pinning_policy

            elif attr == 'hw:cpu_threads_policy':
                cpu_thread_pinning_policy = self._epa.guest.extra_spec_to_mano_cpu_thread_pinning_policy(flavor_info['extra_specs']['hw:cpu_threads_policy'])
                if cpu_thread_pinning_policy is not None:
                    guest_epa.cpu_thread_pinning_policy = cpu_thread_pinning_policy

            elif attr == 'hw:mem_page_size':
                mempage_size = self._epa.guest.extra_spec_to_mano_mempage_size(flavor_info['extra_specs']['hw:mem_page_size'])
                if mempage_size is not None:
                    guest_epa.mempage_size = mempage_size

            elif attr == 'hw:numa_nodes':
                numa_node_count = self._epa.guest.extra_specs_to_mano_numa_node_count(flavor_info['extra_specs']['hw:numa_nodes'])
                if numa_node_count is not None:
                    guest_epa.numa_node_policy.node_cnt = numa_node_count

            elif attr.startswith('hw:numa_cpus.'):
                node_id = attr.split('.')[1]
                nodes = [ n for n in guest_epa.numa_node_policy.node if n.id == int(node_id) ]
                if nodes:
                    numa_node = nodes[0]
                else:
                    numa_node = guest_epa.numa_node_policy.node.add()
                    numa_node.id = int(node_id)

                for x in flavor_info['extra_specs'][attr].split(','):
                   numa_node_vcpu = numa_node.vcpu.add()
                   numa_node_vcpu.id = int(x)

            elif attr.startswith('hw:numa_mem.'):
                node_id = attr.split('.')[1]
                nodes = [ n for n in guest_epa.numa_node_policy.node if n.id == int(node_id) ]
                if nodes:
                    numa_node = nodes[0]
                else:
                    numa_node = guest_epa.numa_node_policy.node.add()
                    numa_node.id = int(node_id)

                numa_node.memory_mb =  int(flavor_info['extra_specs'][attr])

            elif attr == 'hw:numa_mempolicy':
                numa_memory_policy = self._epa.guest.extra_to_mano_spec_numa_memory_policy(flavor_info['extra_specs']['hw:numa_mempolicy'])
                if numa_memory_policy is not None:
                    guest_epa.numa_node_policy.mem_policy = numa_memory_policy

            elif attr == 'trust:trusted_host':
                trusted_execution = self._epa.guest.extra_spec_to_mano_trusted_execution(flavor_info['extra_specs']['trust:trusted_host'])
                if trusted_execution is not None:
                    guest_epa.trusted_execution = trusted_execution

            elif attr == 'pci_passthrough:alias':
                device_types = flavor_info['extra_specs']['pci_passthrough:alias']
                for device in device_types.split(','):
                    dev = guest_epa.pcie_device.add()
                    dev.device_id = device.split(':')[0]
                    dev.count = int(device.split(':')[1])
        return guest_epa

    def parse_host_epa_info(self, flavor_info):
        """
        Parse the flavor_info dictionary (returned by python-client) for host_epa

        Arguments:
           flavor_info: A dictionary object return by novaclient library listing flavor attributes

        Returns:
           host_epa  = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList_HostEpa()
        """
        host_epa  = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList_HostEpa()
        if 'extra_specs' not in flavor_info or flavor_info['extra_specs'] is None:
            return host_epa
        for attr in flavor_info['extra_specs']:
            if attr == 'capabilities:cpu_info:model':
                cpu_model = self._epa.host.extra_specs_to_mano_cpu_model(flavor_info['extra_specs']['capabilities:cpu_info:model'])
                if cpu_model is not None:
                    host_epa.cpu_model = cpu_model

            elif attr == 'capabilities:cpu_info:arch':
                cpu_arch = self._epa.host.extra_specs_to_mano_cpu_arch(flavor_info['extra_specs']['capabilities:cpu_info:arch'])
                if cpu_arch is not None:
                    host_epa.cpu_arch = cpu_arch

            elif attr == 'capabilities:cpu_info:vendor':
                cpu_vendor = self._epa.host.extra_spec_to_mano_cpu_vendor(flavor_info['extra_specs']['capabilities:cpu_info:vendor'])
                if cpu_vendor is not None:
                    host_epa.cpu_vendor = cpu_vendor

            elif attr == 'capabilities:cpu_info:topology:sockets':
                cpu_sockets = self._epa.host.extra_spec_to_mano_cpu_socket_count(flavor_info['extra_specs']['capabilities:cpu_info:topology:sockets'])
                if cpu_sockets is not None:
                    host_epa.cpu_socket_count = cpu_sockets

            elif attr == 'capabilities:cpu_info:topology:cores':
                cpu_cores = self._epa.host.extra_spec_to_mano_cpu_core_count(flavor_info['extra_specs']['capabilities:cpu_info:topology:cores'])
                if cpu_cores is not None:
                    host_epa.cpu_core_count = cpu_cores

            elif attr == 'capabilities:cpu_info:topology:threads':
                cpu_threads = self._epa.host.extra_spec_to_mano_cpu_core_thread_count(flavor_info['extra_specs']['capabilities:cpu_info:topology:threads'])
                if cpu_threads is not None:
                    host_epa.cpu_core_thread_count = cpu_threads

            elif attr == 'capabilities:cpu_info:features':
                cpu_features = self._epa.host.extra_spec_to_mano_cpu_features(flavor_info['extra_specs']['capabilities:cpu_info:features'])
                if cpu_features is not None:
                    for feature in cpu_features:
                        host_epa.cpu_feature.append(feature)
        return host_epa
    
    def parse_host_aggregate_epa_info(self, flavor_info):
        """
        Parse the flavor_info dictionary (returned by python-client) for host_aggregate

        Arguments:
           flavor_info: A dictionary object return by novaclient library listing flavor attributes

        Returns:
           A list of objects host_aggregate of type RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList_HostAggregate()
        """
        host_aggregates = list()
        if 'extra_specs' not in flavor_info or flavor_info['extra_specs'] is None:
            return host_aggregates
        for attr in flavor_info['extra_specs']:
            if attr.startswith('aggregate_instance_extra_specs:'):
                aggregate = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList_HostAggregate()
                aggregate.metadata_key = ":".join(attr.split(':')[1::])
                aggregate.metadata_value = flavor_info['extra_specs'][attr]
                host_aggregates.append(aggregate)
        return host_aggregates
    
        
    def parse_flavor_info(self, flavor_info):
        """
        Parse the flavor_info dictionary and put value in RIFT GI object for flavor
        Arguments:
           flavor_info: A dictionary object returned by novaclient library listing flavor attributes

        Returns: 
           Protobuf GI Object of type RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList()

        """
        flavor = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList()
        if 'name' in flavor_info and flavor_info['name']:
            flavor.name  = flavor_info['name']
        if 'id' in flavor_info and flavor_info['id']:
            flavor.id  = flavor_info['id']

        ### If extra_specs in flavor_info
        if 'extra_specs' in flavor_info:
            flavor.vm_flavor = self.parse_vm_flavor_epa_info(flavor_info)
            flavor.guest_epa = self.parse_guest_epa_info(flavor_info)
            flavor.host_epa = self.parse_host_epa_info(flavor_info)
            for aggr in self.parse_host_aggregate_epa_info(flavor_info):
                ha = flavor.host_aggregate.add()
                ha.from_dict(aggr.as_dict())
        return flavor

    def _match_vm_flavor(self, required, available):
        self.log.info("Matching VM Flavor attributes")
        if available.vcpu_count != required.vcpu_count:
            self.log.debug("VCPU requirement mismatch. Required: %d, Available: %d",
                           required.vcpu_count,
                           available.vcpu_count)
            return False
        if available.memory_mb != required.memory_mb:
            self.log.debug("Memory requirement mismatch. Required: %d MB, Available: %d MB",
                           required.memory_mb,
                           available.memory_mb)
            return False
        if available.storage_gb != required.storage_gb:
            self.log.debug("Storage requirement mismatch. Required: %d GB, Available: %d GB",
                           required.storage_gb,
                           available.storage_gb)
            return False
        self.log.debug("VM Flavor match found")
        return True

    def _match_guest_epa(self, required, available):
        self.log.info("Matching Guest EPA attributes")
        if required.has_field('pcie_device'):
            self.log.debug("Matching pcie_device")
            if available.has_field('pcie_device') == False:
                self.log.debug("Matching pcie_device failed. Not available in flavor")
                return False
            else:
                for dev in required.pcie_device:
                    if not [ d for d in available.pcie_device
                            if ((d.device_id == dev.device_id) and (d.count == dev.count)) ]:
                        self.log.debug("Matching pcie_device failed. Required: %s, Available: %s",
                                       required.pcie_device, available.pcie_device)
                        return False
        elif available.has_field('pcie_device'):
            self.log.debug("Rejecting available flavor because pcie_device not required but available")
            return False


        if required.has_field('mempage_size'):
            self.log.debug("Matching mempage_size")
            if available.has_field('mempage_size') == False:
                self.log.debug("Matching mempage_size failed. Not available in flavor")
                return False
            else:
                if required.mempage_size != available.mempage_size:
                    self.log.debug("Matching mempage_size failed. Required: %s, Available: %s",
                                   required.mempage_size, available.mempage_size)
                    return False
        elif available.has_field('mempage_size'):
            self.log.debug("Rejecting available flavor because mempage_size not required but available")
            return False

        if required.has_field('cpu_pinning_policy'):
            self.log.debug("Matching cpu_pinning_policy")
            if required.cpu_pinning_policy != 'ANY':
                if available.has_field('cpu_pinning_policy') == False:
                    self.log.debug("Matching cpu_pinning_policy failed. Not available in flavor")
                    return False
                else:
                    if required.cpu_pinning_policy != available.cpu_pinning_policy:
                        self.log.debug("Matching cpu_pinning_policy failed. Required: %s, Available: %s",
                                       required.cpu_pinning_policy, available.cpu_pinning_policy)
                        return False
        elif available.has_field('cpu_pinning_policy'):
            self.log.debug("Rejecting available flavor because cpu_pinning_policy not required but available")
            return False

        if required.has_field('cpu_thread_pinning_policy'):
            self.log.debug("Matching cpu_thread_pinning_policy")
            if available.has_field('cpu_thread_pinning_policy') == False:
                self.log.debug("Matching cpu_thread_pinning_policy failed. Not available in flavor")
                return False
            else:
                if required.cpu_thread_pinning_policy != available.cpu_thread_pinning_policy:
                    self.log.debug("Matching cpu_thread_pinning_policy failed. Required: %s, Available: %s",
                                   required.cpu_thread_pinning_policy, available.cpu_thread_pinning_policy)
                    return False
        elif available.has_field('cpu_thread_pinning_policy'):
            self.log.debug("Rejecting available flavor because cpu_thread_pinning_policy not required but available")
            return False

        if required.has_field('trusted_execution'):
            self.log.debug("Matching trusted_execution")
            if required.trusted_execution == True:
                if available.has_field('trusted_execution') == False:
                    self.log.debug("Matching trusted_execution failed. Not available in flavor")
                    return False
                else:
                    if required.trusted_execution != available.trusted_execution:
                        self.log.debug("Matching trusted_execution failed. Required: %s, Available: %s",
                                       required.trusted_execution, available.trusted_execution)
                        return False
        elif available.has_field('trusted_execution'):
            self.log.debug("Rejecting available flavor because trusted_execution not required but available")
            return False

        if required.has_field('numa_node_policy'):
            self.log.debug("Matching numa_node_policy")
            if available.has_field('numa_node_policy') == False:
                self.log.debug("Matching numa_node_policy failed. Not available in flavor")
                return False
            else:
                if required.numa_node_policy.has_field('node_cnt'):
                    self.log.debug("Matching numa_node_policy node_cnt")
                    if available.numa_node_policy.has_field('node_cnt') == False:
                        self.log.debug("Matching numa_node_policy node_cnt failed. Not available in flavor")
                        return False
                    else:
                        if required.numa_node_policy.node_cnt != available.numa_node_policy.node_cnt:
                            self.log.debug("Matching numa_node_policy node_cnt failed. Required: %s, Available: %s",
                                           required.numa_node_policy.node_cnt, available.numa_node_policy.node_cnt)
                            return False
                elif available.numa_node_policy.has_field('node_cnt'):
                    self.log.debug("Rejecting available flavor because numa node count not required but available")
                    return False

                if required.numa_node_policy.has_field('mem_policy'):
                    self.log.debug("Matching numa_node_policy mem_policy")
                    if available.numa_node_policy.has_field('mem_policy') == False:
                        self.log.debug("Matching numa_node_policy mem_policy failed. Not available in flavor")
                        return False
                    else:
                        if required.numa_node_policy.mem_policy != available.numa_node_policy.mem_policy:
                            self.log.debug("Matching numa_node_policy mem_policy failed. Required: %s, Available: %s",
                                           required.numa_node_policy.mem_policy, available.numa_node_policy.mem_policy)
                            return False
                elif available.numa_node_policy.has_field('mem_policy'):
                    self.log.debug("Rejecting available flavor because num node mem_policy not required but available")
                    return False

                if required.numa_node_policy.has_field('node'):
                    self.log.debug("Matching numa_node_policy nodes configuration")
                    if available.numa_node_policy.has_field('node') == False:
                        self.log.debug("Matching numa_node_policy nodes configuration failed. Not available in flavor")
                        return False
                    for required_node in required.numa_node_policy.node:
                        self.log.debug("Matching numa_node_policy nodes configuration for node %s",
                                       required_node)
                        numa_match = False
                        for available_node in available.numa_node_policy.node:
                            if required_node.id != available_node.id:
                                self.log.debug("Matching numa_node_policy nodes configuration failed. Required: %s, Available: %s",
                                               required_node, available_node)
                                continue
                            if required_node.vcpu != available_node.vcpu:
                                self.log.debug("Matching numa_node_policy nodes configuration failed. Required: %s, Available: %s",
                                               required_node, available_node)
                                continue
                            if required_node.memory_mb != available_node.memory_mb:
                                self.log.debug("Matching numa_node_policy nodes configuration failed. Required: %s, Available: %s",
                                               required_node, available_node)
                                continue
                            numa_match = True
                        if numa_match == False:
                            return False
                elif available.numa_node_policy.has_field('node'):
                    self.log.debug("Rejecting available flavor because numa nodes not required but available")
                    return False
        elif available.has_field('numa_node_policy'):
            self.log.debug("Rejecting available flavor because numa_node_policy not required but available")
            return False
        self.log.info("Successful match for Guest EPA attributes")
        return True

    def _match_vswitch_epa(self, required, available):
        self.log.debug("VSwitch EPA match found")
        return True

    def _match_hypervisor_epa(self, required, available):
        self.log.debug("Hypervisor EPA match found")
        return True

    def _match_host_epa(self, required, available):
        self.log.info("Matching Host EPA attributes")
        if required.has_field('cpu_model'):
            self.log.debug("Matching CPU model")
            if available.has_field('cpu_model') == False:
                self.log.debug("Matching CPU model failed. Not available in flavor")
                return False
            else:
                #### Convert all PREFER to REQUIRE since flavor will only have REQUIRE attributes
                if required.cpu_model.replace('PREFER', 'REQUIRE') != available.cpu_model:
                    self.log.debug("Matching CPU model failed. Required: %s, Available: %s",
                                   required.cpu_model, available.cpu_model)
                    return False
        elif available.has_field('cpu_model'):
            self.log.debug("Rejecting available flavor because cpu_model not required but available")
            return False

        if required.has_field('cpu_arch'):
            self.log.debug("Matching CPU architecture")
            if available.has_field('cpu_arch') == False:
                self.log.debug("Matching CPU architecture failed. Not available in flavor")
                return False
            else:
                #### Convert all PREFER to REQUIRE since flavor will only have REQUIRE attributes
                if required.cpu_arch.replace('PREFER', 'REQUIRE') != available.cpu_arch:
                    self.log.debug("Matching CPU architecture failed. Required: %s, Available: %s",
                                   required.cpu_arch, available.cpu_arch)
                    return False
        elif available.has_field('cpu_arch'):
            self.log.debug("Rejecting available flavor because cpu_arch not required but available")
            return False

        if required.has_field('cpu_vendor'):
            self.log.debug("Matching CPU vendor")
            if available.has_field('cpu_vendor') == False:
                self.log.debug("Matching CPU vendor failed. Not available in flavor")
                return False
            else:
                #### Convert all PREFER to REQUIRE since flavor will only have REQUIRE attributes
                if required.cpu_vendor.replace('PREFER', 'REQUIRE') != available.cpu_vendor:
                    self.log.debug("Matching CPU vendor failed. Required: %s, Available: %s",
                                   required.cpu_vendor, available.cpu_vendor)
                    return False
        elif available.has_field('cpu_vendor'):
            self.log.debug("Rejecting available flavor because cpu_vendor not required but available")
            return False

        if required.has_field('cpu_socket_count'):
            self.log.debug("Matching CPU socket count")
            if available.has_field('cpu_socket_count') == False:
                self.log.debug("Matching CPU socket count failed. Not available in flavor")
                return False
            else:
                if required.cpu_socket_count != available.cpu_socket_count:
                    self.log.debug("Matching CPU socket count failed. Required: %s, Available: %s",
                                   required.cpu_socket_count, available.cpu_socket_count)
                    return False
        elif available.has_field('cpu_socket_count'):
            self.log.debug("Rejecting available flavor because cpu_socket_count not required but available")
            return False

        if required.has_field('cpu_core_count'):
            self.log.debug("Matching CPU core count")
            if available.has_field('cpu_core_count') == False:
                self.log.debug("Matching CPU core count failed. Not available in flavor")
                return False
            else:
                if required.cpu_core_count != available.cpu_core_count:
                    self.log.debug("Matching CPU core count failed. Required: %s, Available: %s",
                                   required.cpu_core_count, available.cpu_core_count)
                    return False
        elif available.has_field('cpu_core_count'):
            self.log.debug("Rejecting available flavor because cpu_core_count not required but available")
            return False

        if required.has_field('cpu_core_thread_count'):
            self.log.debug("Matching CPU core thread count")
            if available.has_field('cpu_core_thread_count') == False:
                self.log.debug("Matching CPU core thread count failed. Not available in flavor")
                return False
            else:
                if required.cpu_core_thread_count != available.cpu_core_thread_count:
                    self.log.debug("Matching CPU core thread count failed. Required: %s, Available: %s",
                                   required.cpu_core_thread_count, available.cpu_core_thread_count)
                    return False
        elif available.has_field('cpu_core_thread_count'):
            self.log.debug("Rejecting available flavor because cpu_core_thread_count not required but available")
            return False

        if required.has_field('cpu_feature'):
            self.log.debug("Matching CPU feature list")
            if available.has_field('cpu_feature') == False:
                self.log.debug("Matching CPU feature list failed. Not available in flavor")
                return False
            else:
                for feature in required.cpu_feature:
                    if feature not in available.cpu_feature:
                        self.log.debug("Matching CPU feature list failed. Required feature: %s is not present. Available features: %s",
                                       feature, available.cpu_feature)
                        return False
        elif available.has_field('cpu_feature'):
            self.log.debug("Rejecting available flavor because cpu_feature not required but available")
            return False
        self.log.info("Successful match for Host EPA attributes")
        return True


    def _match_placement_group_inputs(self, required, available):
        self.log.info("Matching Host aggregate attributes")

        if not required and not available:
            # Host aggregate not required and not available => success
            self.log.info("Successful match for Host Aggregate attributes")
            return True
        if required and available:
            # Host aggregate requested and available => Do a match and decide
            xx = [ x.as_dict() for x in required ]
            yy = [ y.as_dict() for y in available ]
            for i in xx:
                if i not in yy:
                    self.log.debug("Rejecting available flavor because host Aggregate mismatch. Required: %s, Available: %s",
                                   required, available)
                    return False
            self.log.info("Successful match for Host Aggregate attributes")
            return True
        else:
            # Either of following conditions => Failure
            #  - Host aggregate required but not available
            #  - Host aggregate not required but available
            self.log.debug("Rejecting available flavor because host Aggregate mismatch. Required: %s, Available: %s",
                           required, available)
            return False
    

    def _match_epa_params(self, resource_info, request_params):
        """
        Match EPA attributes
        Arguments:
           resource_info: Protobuf GI object RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList()
                          Following attributes would be accessed
                          - vm_flavor
                          - guest_epa
                          - host_epa
                          - host_aggregate

           request_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams(). 
                          Following attributes would be accessed
                          - vm_flavor
                          - guest_epa
                          - host_epa
                          - host_aggregate
        Returns:
           True -- Match between resource_info and request_params
           False -- No match between resource_info and request_params
        """
        result = False
        result = self._match_vm_flavor(getattr(request_params, 'vm_flavor'),
                                       getattr(resource_info, 'vm_flavor'))
        if result == False:
            self.log.debug("VM Flavor mismatched")
            return False

        result = self._match_guest_epa(getattr(request_params, 'guest_epa'),
                                       getattr(resource_info, 'guest_epa'))
        if result == False:
            self.log.debug("Guest EPA mismatched")
            return False

        result = self._match_vswitch_epa(getattr(request_params, 'vswitch_epa'),
                                         getattr(resource_info, 'vswitch_epa'))
        if result == False:
            self.log.debug("Vswitch EPA mismatched")
            return False

        result = self._match_hypervisor_epa(getattr(request_params, 'hypervisor_epa'),
                                            getattr(resource_info, 'hypervisor_epa'))
        if result == False:
            self.log.debug("Hypervisor EPA mismatched")
            return False

        result = self._match_host_epa(getattr(request_params, 'host_epa'),
                                      getattr(resource_info, 'host_epa'))
        if result == False:
            self.log.debug("Host EPA mismatched")
            return False

        result = self._match_placement_group_inputs(getattr(request_params, 'host_aggregate'),
                                                    getattr(resource_info, 'host_aggregate'))

        if result == False:
            self.log.debug("Host Aggregate mismatched")
            return False

        return True

    def match_resource_flavor(self, vdu_init, flavor_list):
        """
        Arguments:
           vdu_init: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams(). 
           flavor_list: List of Protobuf GI object RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList()

        Returns:
           Flavor_ID -- If match is found between vdu_init and one of flavor_info from flavor_list
           None -- No match between vdu_init and one of flavor_info from flavor_list

        Select a existing flavor if it matches the request or create new flavor
        """
        for flv in flavor_list:
            self.log.info("Attempting to match compute requirement for VDU: %s with flavor %s",
                          vdu_init.name, flv)
            if self._match_epa_params(flv, vdu_init):
                self.log.info("Flavor match found for compute requirements for VDU: %s with flavor name: %s, flavor-id: %s",
                              vdu_init.name, flv.name, flv.id)
                return flv.id
        return None

