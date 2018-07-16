############################################################################
# Copyright 2016 RIFT.io Inc                                               #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License");          #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http://www.apache.org/licenses/LICENSE-2.0                           #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################

import argparse
import asyncio
import logging
import os
import ssl

import juju.loop
from juju.controller import Controller
from juju.model import Model, ModelObserver

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python doesn't verify by default (see pep-0476)
    #   https://www.python.org/dev/peps/pep-0476/
    pass


class JujuVersionError(Exception):
    pass


class JujuApiError(Exception):
    pass


class JujuEnvError(JujuApiError):
    pass


class JujuModelError(JujuApiError):
    pass


class JujuStatusError(JujuApiError):
    pass


class JujuUnitsError(JujuApiError):
    pass


class JujuWaitUnitsError(JujuApiError):
    pass


class JujuSrvNotDeployedError(JujuApiError):
    pass


class JujuAddCharmError(JujuApiError):
    pass


class JujuDeployError(JujuApiError):
    pass


class JujuDestroyError(JujuApiError):
    pass


class JujuResolveError(JujuApiError):
    pass


class JujuActionError(JujuApiError):
    pass


class JujuActionApiError(JujuActionError):
    pass


class JujuActionInfoError(JujuActionError):
    pass


class JujuActionExecError(JujuActionError):
    pass


class JujuAuthenticationError(Exception):
    pass


class JujuMonitor(ModelObserver):
    """Monitor state changes within the Juju Model."""
    # async def on_change(self, delta, old, new, model):
    #     """React to changes in the Juju model."""
    #
    #     # TODO: Setup the hook to update the UI if the status of a unit changes
    #     # to be used when deploying a charm and waiting for it to be "ready"
    #     if delta.entity in ['application', 'unit'] and delta.type == "change":
    #         pass
    #
    #     # TODO: Add a hook when an action is complete

    pass


class JujuApi(object):
    """JujuApi wrapper on jujuclient library.

    There should be one instance of JujuApi for each VNF manged by Juju.

    Assumption:
        Currently we use one unit per service/VNF. So once a service
        is deployed, we store the unit name and reuse it
    """

    log = None
    controller = None
    models = {}
    model = None
    model_name = None
    model_uuid = None
    authenticated = False

    def __init__(self,
                 log=None,
                 loop=None,
                 server='127.0.0.1',
                 port=17070,
                 user='admin',
                 secret=None,
                 version=None,
                 model_name='default',
                 ):
        """Initialize with the Juju credentials."""

        if log:
            self.log = log
        else:
            self.log = logging.getLogger(__name__)

        # Quiet websocket traffic
        logging.getLogger('websockets.protocol').setLevel(logging.INFO)

        self.log.debug('JujuApi: instantiated')

        self.server = server
        self.port = port

        self.secret = secret
        if user.startswith('user-'):
            self.user = user
        else:
            self.user = 'user-{}'.format(user)

        self.endpoint = '%s:%d' % (server, int(port))

        self.model_name = model_name

        if loop:
            self.loop = loop

    def __del__(self):
        """Close any open connections."""
        yield self.logout()

    async def apply_config(self, config, application):
        """Apply a configuration to the application."""
        self.log.debug("JujuApi: Applying configuration to {}.".format(
            application
        ))
        return await self.set_config(application=application, config=config)

    async def deploy_application(self, charm, name="", path=""):
        """Deploy an application."""
        if not self.authenticated:
            await self.login()

        # Check that the charm is valid and exists.
        if charm is None:
            return None

        app = await self.get_application(name)
        if app is None:
            # TODO: Handle the error if the charm isn't found.
            self.log.debug("JujuApi: Deploying charm {} ({}) from {}".format(
                charm,
                name,
                path,
            ))
            app = await self.model.deploy(
                path,
                application_name=name,
                series='xenial',
            )
        return app
    deploy_service = deploy_application

    async def get_action_status(self, uuid):
        """Get the status of an action."""
        if not self.authenticated:
            await self.login()

        self.log.debug("JujuApi: Waiting for status of action uuid {}".format(uuid))
        action = await self.model.wait_for_action(uuid)
        return action.status

    async def get_application(self, application):
        """Get the deployed application."""
        if not self.authenticated:
            await self.login()

        self.log.debug("JujuApi: Getting application {}".format(application))
        app = None
        if application and self.model:
            if self.model.applications:
                if application in self.model.applications:
                    app = self.model.applications[application]
        return app

    async def get_application_status(self, application):
        """Get the status of an application."""
        if not self.authenticated:
            await self.login()

        status = None
        app = await self.get_application(application)
        if app:
            status = app.status
            self.log.debug("JujuApi: Status of application {} is {}".format(
                application,
                str(status),
            ))
        return status
    get_service_status = get_application_status

    async def get_config(self, application):
        """Get the configuration of an application."""
        if not self.authenticated:
            await self.login()

        config = None
        app = await self.get_application(application)
        if app:
            config = await app.get_config()

        self.log.debug("JujuApi: Config of application {} is {}".format(
            application,
            str(config),
        ))

        return config

    async def get_model(self, name='default'):
        """Get a model from the Juju Controller.

        Note: Model objects returned must call disconnected() before it goes
        out of scope."""
        if not self.authenticated:
            await self.login()

        model = Model()

        uuid = await self.get_model_uuid(name)

        self.log.debug("JujuApi: Connecting to model {} ({})".format(
            model,
            uuid,
        ))

        await model.connect(
            self.endpoint,
            uuid,
            self.user,
            self.secret,
            None,
        )

        return model

    async def get_model_uuid(self, name='default'):
        """Get the UUID of a model.

        Iterate through all models in a controller and find the matching model.
        """
        if not self.authenticated:
            await self.login()

        uuid = None

        models = await self.controller.get_models()

        self.log.debug("JujuApi: Looking through {} models for model {}".format(
            len(models.user_models),
            name,
        ))
        for model in models.user_models:
            if model.model.name == name:
                uuid = model.model.uuid
                break

        return uuid

    async def get_status(self):
        """Get the model status."""
        if not self.authenticated:
            await self.login()

        if not self.model:
            self.model = self.get_model(self.model_name)

        class model_state:
            applications = {}
            machines = {}
            relations = {}

        self.log.debug("JujuApi: Getting model status")
        status = model_state()
        status.applications = self.model.applications
        status.machines = self.model.machines

        return status

    async def is_application_active(self, application):
        """Check if the application is in an active state."""
        if not self.authenticated:
            await self.login()

        state = False
        status = await self.get_application_status(application)
        if status and status in ['active']:
            state = True

        self.log.debug("JujuApi: Application {} is {} active".format(
            application,
            "" if status else "not",
        ))

        return state
    is_service_active = is_application_active

    async def is_application_blocked(self, application):
        """Check if the application is in a blocked state."""
        if not self.authenticated:
            await self.login()

        state = False
        status = await self.get_application_status(application)
        if status and status in ['blocked']:
            state = True

        self.log.debug("JujuApi: Application {} is {} blocked".format(
            application,
            "" if status else "not",
        ))

        return state
    is_service_blocked = is_application_blocked

    async def is_application_deployed(self, application):
        """Check if the application is in a deployed state."""
        if not self.authenticated:
            await self.login()

        state = False
        status = await self.get_application_status(application)
        if status and status in ['active']:
            state = True
        self.log.debug("JujuApi: Application {} is {} deployed".format(
            application,
            "" if status else "not",
        ))

        return state
    is_service_deployed = is_application_deployed

    async def is_application_error(self, application):
        """Check if the application is in an error state."""
        if not self.authenticated:
            await self.login()

        state = False
        status = await self.get_application_status(application)
        if status and status in ['error']:
            state = True
        self.log.debug("JujuApi: Application {} is {} errored".format(
            application,
            "" if status else "not",
        ))

        return state
    is_service_error = is_application_error

    async def is_application_maint(self, application):
        """Check if the application is in a maintenance state."""
        if not self.authenticated:
            await self.login()

        state = False
        status = await self.get_application_status(application)
        if status and status in ['maintenance']:
            state = True
        self.log.debug("JujuApi: Application {} is {} in maintenence".format(
            application,
            "" if status else "not",
        ))

        return state
    is_service_maint = is_application_maint

    async def is_application_up(self, application=None):
        """Check if the application is up."""
        if not self.authenticated:
            await self.login()
        state = False

        status = await self.get_application_status(application)
        if status and status in ['active', 'blocked']:
            state = True
        self.log.debug("JujuApi: Application {} is {} up".format(
            application,
            "" if status else "not",
        ))
        return state
    is_service_up = is_application_up

    async def login(self):
        """Login to the Juju controller."""
        if self.authenticated:
            return
        cacert = None
        self.controller = Controller()

        self.log.debug("JujuApi: Logging into controller")

        if self.secret:
            await self.controller.connect(
                self.endpoint,
                self.user,
                self.secret,
                cacert,
            )
        else:
            await self.controller.connect_current()

        self.authenticated = True
        self.model = await self.get_model(self.model_name)

    async def logout(self):
        """Logout of the Juju controller."""
        if not self.authenticated:
            return

        if self.model:
            await self.model.disconnect()
            self.model = None
        if self.controller:
            await self.controller.disconnect()
            self.controller = None

        self.authenticated = False

    async def remove_application(self, name):
        """Remove the application."""
        if not self.authenticated:
            await self.login()

        app = await self.get_application(name)
        if app:
            self.log.debug("JujuApi: Destroying application {}".format(
                name,
            ))

            await app.destroy()

    async def resolve_error(self, application=None):
        """Resolve units in error state."""
        if not self.authenticated:
            await self.login()

        app = await self.get_application(application)
        if app:
            self.log.debug("JujuApi: Resolving errors for application {}".format(
                application,
            ))

            for unit in app.units:
                app.resolved(retry=True)

    async def run_action(self, application, action_name, **params):
        """Execute an action and return an Action object."""
        if not self.authenticated:
            await self.login()
        result = {
            'status': '',
            'action': {
                'tag': None,
                'results': None,
            }
        }
        app = await self.get_application(application)
        if app:
            # We currently only have one unit per application
            # so use the first unit available.
            unit = app.units[0]

            self.log.debug("JujuApi: Running Action {} against Application {}".format(
                action_name,
                application,
            ))

            action = await unit.run_action(action_name, **params)

            # Wait for the action to complete
            await action.wait()

            result['status'] = action.status
            result['action']['tag'] = action.data['id']
            result['action']['results'] = action.results

        return result
    execute_action = run_action

    async def set_config(self, application, config):
        """Apply a configuration to the application."""
        if not self.authenticated:
            await self.login()

        app = await self.get_application(application)
        if app:
            self.log.debug("JujuApi: Setting config for Application {}".format(
                application,
            ))
            await app.set_config(config)

            # Verify the config is set
            newconf = await app.get_config()
            for key in config:
                if config[key] != newconf[key]:
                    self.log.debug("JujuApi: Config not set! Key {} Value {} doesn't match {}".format(key, config[key], newconf[key]))


    async def set_parameter(self, parameter, value, application=None):
        """Set a config parameter for a service."""
        if not self.authenticated:
            await self.login()

        self.log.debug("JujuApi: Setting {}={} for Application {}".format(
            parameter,
            value,
            application,
        ))
        return await self.apply_config(
            {parameter: value},
            application=application,
        )

    async def wait_for_application(self, name, timeout=300):
        """Wait for an application to become active."""
        if not self.authenticated:
            await self.login()

        app = await self.get_application(name)
        if app:
            self.log.debug("JujuApi: Waiting {} seconds for Application {}".format(
                timeout,
                name,
            ))

            await self.model.block_until(
                lambda: all(
                    unit.agent_status == 'idle'
                    and unit.workload_status
                    in ['active', 'unknown'] for unit in app.units
                    ),
                timeout=timeout,
                )


def get_argparser():
    parser = argparse.ArgumentParser(description='Test Juju')
    parser.add_argument(
        "-s", "--server",
        default='10.0.202.49',
        help="Juju controller"
    )
    parser.add_argument(
        "-u", "--user",
        default='admin',
        help="User, default user-admin"
    )
    parser.add_argument(
        "-p", "--password",
        default='',
        help="Password for the user"
    )
    parser.add_argument(
        "-P", "--port",
        default=17070,
        help="Port number, default 17070"
    )
    parser.add_argument(
        "-d", "--directory",
        help="Local directory for the charm"
    )
    parser.add_argument(
        "--application",
        help="Charm name"
    )
    parser.add_argument(
        "--vnf-ip",
        help="IP of the VNF to configure"
    )
    parser.add_argument(
        "-m", "--model",
        default='default',
        help="The model to connect to."
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_argparser()

    # Set logging level to debug so we can see verbose output from the
    # juju library.
    logging.basicConfig(level=logging.DEBUG)

    # Quiet logging from the websocket library. If you want to see
    # everything sent over the wire, set this to DEBUG.
    ws_logger = logging.getLogger('websockets.protocol')
    ws_logger.setLevel(logging.INFO)

    endpoint = '%s:%d' % (args.server, int(args.port))

    loop = asyncio.get_event_loop()

    api = JujuApi(server=args.server,
                  port=args.port,
                  user=args.user,
                  secret=args.password,
                  loop=loop,
                  log=ws_logger,
                  model_name=args.model
                  )

    juju.loop.run(api.login())

    status = juju.loop.run(api.get_status())

    print('Applications:', list(status.applications.keys()))
    print('Machines:', list(status.machines.keys()))

    if args.directory and args.application:
        # Deploy the charm
        charm = os.path.basename(args.directory)
        juju.loop.run(
            api.deploy_application(charm,
                                   name=args.application,
                                   path=args.directory,
                                   )
        )

        juju.loop.run(api.wait_for_application(charm))

        # Wait for the service to come up
        up = juju.loop.run(api.is_application_up(charm))
        print("Application is {}".format("up" if up else "down"))

        print("Service {} is deployed".format(args.application))

        ###########################
        # Execute config on charm #
        ###########################
        config = juju.loop.run(api.get_config(args.application))
        hostname = config['ssh-username']['value']
        rhostname = hostname[::-1]

        # Apply the configuration
        juju.loop.run(api.apply_config(
            {'ssh-username': rhostname}, application=args.application
        ))

        # Get the configuration
        config = juju.loop.run(api.get_config(args.application))

        # Verify the configuration has been updated
        assert(config['ssh-username']['value'] == rhostname)

        ####################################
        # Get the status of an application #
        ####################################
        status = juju.loop.run(api.get_application_status(charm))
        print("Application Status: {}".format(status))

        ###########################
        # Execute a simple action #
        ###########################
        result = juju.loop.run(api.run_action(charm, 'get-ssh-public-key'))
        print("Action {} status is {} and returned {}".format(
            result['status'],
            result['action']['tag'],
            result['action']['results']
        ))

        #####################################
        # Execute an action with parameters #
        #####################################
        result = juju.loop.run(
            api.run_action(charm, 'run', command='hostname')
        )
        print("Action {} status is {} and returned {}".format(
            result['status'],
            result['action']['tag'],
            result['action']['results']
        ))

    juju.loop.run(api.logout())

    loop.close()

    #     if args.vnf_ip and \
    #        ('clearwater-aio' in args.directory):
    #         # Execute config on charm
    #         api._apply_config({'proxied_ip': args.vnf_ip})
    #
    #         while not api._is_service_active():
    #             time.sleep(10)
    #
    #         print ("Service {} is in status {}".
    #                format(args.service, api._get_service_status()))
    #
    #         res = api._execute_action('create-update-user', {'number': '125252352525',
    #                                                          'password': 'asfsaf'})
    #
    #         print ("Action 'creat-update-user response: {}".format(res))
    #
    #         status = res['status']
    #         while status not in [ 'completed', 'failed' ]:
    #             time.sleep(2)
    #             status = api._get_action_status(res['action']['tag'])['status']
    #
    #             print("Action status: {}".format(status))
    #
    #         # This action will fail as the number is non-numeric
    #         res = api._execute_action('delete-user', {'number': '125252352525asf'})
    #
    #         print ("Action 'delete-user response: {}".format(res))
    #
    #         status = res['status']
    #         while status not in [ 'completed', 'failed' ]:
    #             time.sleep(2)
    #             status = api._get_action_status(res['action']['tag'])['status']
    #
    #             print("Action status: {}".format(status))
