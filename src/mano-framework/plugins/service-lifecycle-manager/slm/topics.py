# With gatekeeper
GK_CREATE = "service.instances.create"
GK_PAUSE = "service.instance.pause"
GK_RESUME = "service.instance.restart"
GK_KILL = "service.instance.terminate"
GK_UPDATE = "service.instances.update"

# With other SLM
MANO_STATE = "mano.share.state"
MANO_CREATE = "mano.instances.create"
MANO_PAUSE = "mano.instance.pause"
MANO_RESUME = "mano.instance.restart"
MANO_KILL = "mano.instance.terminate"
MANO_UPDATE = "mano.instances.update"
MANO_DEPLOY = "mano.function.deploy"
MANO_DEPLOY_KUBERNETES = "mano.function.kubernetes.deploy"
MANO_PLACE = "mano.service.place"
MANO_START = "mano.function.start"
MANO_CONFIG = "mano.function.configure"
MANO_STOP = "mano.function.stop"
MANO_SCALE = "mano.function.scale"

# With gatekeeper or other SLM
WC_CREATE = "*.instances.create"
WC_PAUSE = "*.instance.pause"
WC_RESUME = "*.instance.restart"
WC_KILL = "*.instance.terminate"
WC_UPDATE = "*.instances.update"

# With infrastructure adaptor
IA_DEPLOY = "infrastructure.function.deploy"
IA_REMOVE = "infrastructure.service.remove"
IA_TOPOLOGY = "infrastructure.management.compute.list"
IA_PREPARE = "infrastructure.service.prepare"
IA_CONF_CHAIN = "infrastructure.service.chain.configure"
IA_DECONF_CHAIN = "infrastructure.service.chain.deconfigure"
IA_CONF_WAN = "infrastructure.service.wan.configure"
IA_DECONF_WAN = "infrastructure.service.wan.deconfigure"

# With specific manager registry
SRM_ONBOARD = "specific.manager.registry.ssm.on-board"
SRM_INSTANT = "specific.manager.registry.ssm.instantiate"
SRM_UPDATE = "specific.manager.registry.ssm.update"
SSM_TERM = "specific.manager.registry.ssm.terminate"
FSM_TERM = "specific.manager.registry.fsm.terminate"

# with sdn plugin
MANO_CHAIN_DPLOY = "chain.dploy.sdnplugin"

# With Executive
EXEC_PLACE = "placement.executive.request"

# With plugin mananger
PL_STATUS = "platform.management.plugin.status"

# With monitoring
MON_RECEIVE = "son.monitoring"
FROM_MON_SSM = "monitor.ssm."
