# [SONATA](http://www.sonata-nfv.eu)'s Keycloak server
[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gkeeper)](http://jenkins.sonata-nfv.eu/job/son-gkeeper)

This folder includes the configuration and deployment specifications of **Keycloak** identity management and **User Management** handshaking.

Keycloak is a key component to enable authentication and authorization features for the Service Platform.

## Architecture
The son-keycloak will enable identity and access management for SONATA Service Platform components. To be used as a part of infrastructure the following was considered:
* It requires an adapter in the Gatekeeper API, which **son-gtkusr** implements.
* It is located behind the Gatekeeper API and User Management micro-service. 
* It will be expose a REST API which is required by the **son-gtkusr**.
* It is supported by a MongoDB connected to the User Management micro-service.

```

            +----------------+         +---------------+          +---------------+
            |                |         |               |          |               |
   +--------+   son-gtkapi   +--------->   son-gtkusr  |+--------->    keycloak   |
            |                |         |               |          |               |
            +----------------+         +---------------+          +---------------+
                                               |
                                               |                  +---------------+
                                               |                  |               |
                                               +------------------>   son-mongo   |
                                                                  |               |
                                                                  +---------------+
```
## Configuration
The configuration and deployment settings are composed of different files:
* The **supervisord.conf** file
* The **create_predefined_entities.sh** script file

### supervisord.conf
It is responsible for the launch of the Keycloak server and it is executed by the provided Dockerfile. 
- **-Djboss.socket.binding.port-offset=-2479** parameter defines the port that Keycloak will be using. It is set to **5601** by default (8080-2479)

### create_predefined_entities.sh
This script configures the User Management adapter and the required entities in Keycloak.
Important settings are listed below:
- KEYCLOAK_USER=admin (by default)
- KEYCLOAK_PASSWORD=admin (by default)
- SONATA_USER=sonata (by default)
- SONATA_PASSWORD=sonata (by default)
- SONATA_EMAIL=sonata.admin@email.com (by default, it must be changed)
- KEYCLOAK_PORT=5601
- KEYCLOAK_URL=http://localhost:$KEYCLOAK_PORT
- KEYCLOAK_OPENID_TOKEN_ENDPOINT=$KEYCLOAK_URL/auth/realms/sonata/protocol/openid-connect/token
- ADAPTER_URL=http://son-gtkusr:5600/api/v1/config
- ADAPTER_ADMIN=http://son-gtkusr:5600/admin
- KCADMIN_SCRIPT=/opt/jboss/keycloak/bin/kcadm.sh
- SONATA_REALM=sonata
- ADAPTER_CLIENT=adapter

It is recommended to leave the settings as default in order to avoid breaking the negotiation between Keycloak and the User Management adapter.

## Usage
To run this module you can do it by this way:

```sh
$ docker run --name son-keycloak -d -p 5601:5601 --net=sonata --network-alias=son-keycloak -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin  -e SONATA_USER=sonata -e SONATA_PASSWORD=1234 -e SONATA_EMAIL=sonata.admin@email.com --log-driver=gelf --log-opt gelf-address=udp://10.30.0.219:12900 registry.sonata-nfv.eu:5000/son-keycloak

```

OPTIONS:
* --name = Container name
* --net = Network with the other Service Platform components
* -p = 5601:5601 External port 5601 -> Internal port 5601
* -e = KEYCLOAK_USER and KEYCLOAK_PASSWORD creates the default "master" admin user required by Keycloak. If they are not provided, admin/admin are set by default
* -e = SONATA_USER and SONATA_PASSWORD creates the default SONATA realm admin user. If they are not provided, sonata/sonata are set by default
* -e = SONATA_EMAIL sets the email address to the default SONATA realm admin user. It must be set in order to be effective

## Documentation
Information about Keycloak can be found in [`Keycloak Documentation`](http://www.keycloak.org/documentation.html) section.
You can refer to the [`Gatekeeper Github Wiki`](https://github.com/sonata-nfv/son-gkeeper/wiki) sections and check for User Management pages, which include information and examples of usage of its features.

## License
The license of the SONATA Gatekeeper is Apache 2.0 (please see the [license](https://github.com/sonata-nfv/son-editorgkeeper/blob/master/LICENSE) file).

---
#### Lead Developers

The following lead developers are responsible for this micro-service and have admin rights. They can, for example, merge pull requests.

* Felipe Vicens ([felipevicens](https://github.com/felipevicens))
* Daniel Guija ([dang03](https://github.com/dang03))

#### Feedback-Chanels

Please use the [GitHub issues](https://github.com/sonata-nfv/son-gkeeper/issues) and the SONATA development mailing list `sonata-dev@lists.atosresearch.eu` for feedback.

