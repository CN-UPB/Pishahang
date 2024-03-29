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

from flm_base.plugin import FunctionLifecycleManagerBasePlugin
from klm import version


class KubernetesLifecycleManager(FunctionLifecycleManagerBasePlugin):
    """
    Kubernetes Function Lifecycle Manager Plugin
    """

    def __init__(self, **kwargs):
        super().__init__(
            version=version,
            description="Kubernetes Function Lifecycle Manager Plugin",
            **kwargs
        )

    northbound_topics = {
        **FunctionLifecycleManagerBasePlugin.northbound_topics,
        "deploy": "mano.function.kubernetes.deploy",
    }


def main():
    KubernetesLifecycleManager()
