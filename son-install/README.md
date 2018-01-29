<p align="center"><img src="https://github.com/sonata-nfv/son-install/wiki/images/sonata_logo_400px.png" /></p>

# son-install

'son-install' provides a simple way to Create, Manage, Upgrade and Destroy (CMUD) SONATA resources for the Service Plataform (SP) as a standalone machine 

'son-install' is built on a set of Ansible playbooks that aims to:
* automate the deployment of the SONATA SP
* manage the SP services and applications lifecycle
* zero downtime roll up upgrades

All you need is a 'bash' shell with Ansible installed to run 'son-cmud.yml', ie, all the SONATA CMUD operations can be executed in a single line command



## What's new in Release 2.1
* application versioning - you can now choose the SP version to deployment, eg:  'latest', '2.1' or 'dev'


## What's new in Release 2.0

Deploy the platform from the scratch for a specific environment (integration, qualification, demonstration)
* step 1: provision infrastrucutre
* step 2: standardize configurations
* step 3: install applications and services


##  Characteristics

* Multi-Stage: deploy the Integration, Qualification and Demonstration environments
* Multi-PoP: deploy to multiple sites (set the right credential variables)
* Multi-VIM: Openstack (AWS under evaluation, OSM under evaluation)
* Multi-Distro: Ubuntu 14.04, Ubuntu 16.04, CentOS 7
* Multi-Operations: Create, Manage, Upgrade, Destroy


## Requirements

* Ansible 2.3.0+
* Shade 1.16.0+


## Usage

The structure of 'son-install' is flexible enough to:
* deploy and manage a single service or application to an existing machine
* deploy, manage, upgrade, destroy a complex distributed platform


### Deploying to LOCAL machine

#### Deployment

A quick way to deploy SONATA 5G NFV SP to the local machine is:
On a fresh ubuntu xenial installation
```
 sudo apt-get install -y software-properties-common
 sudo apt-add-repository -y ppa:ansible/ansible
 sudo apt-get update
 sudo apt-get install -y ansible
 sudo apt-get install -y git
 git clone https://github.com/sonata-nfv/son-install.git
 cd son-install
 echo sonata | tee ~/.ssh/.vault_pass
 ansible-playbook utils/deploy/sp.yml -e "target=localhost public_ip=<your_ip4_address>" -v
```
where:
* public_ip: is the IP address of the (local) guest machine, ie, the Floating IP in Openstack lingo

[![asciicast](https://asciinema.org/a/44MwPYliuOxxYBFkkm7M8eqM4.png)](https://asciinema.org/a/44MwPYliuOxxYBFkkm7M8eqM4)


### Openstack VIM: Provisioning infrastructure and deploying software

The complete way to deploy and manage SONATA 5G NFV services and application from the scratch, ie, first provisioning the infrastructure resources and then deploying the software


#### Pre-configuration

1. The SP database passwords are encrypted - you MUST create an external file "~/.ssh/.vault_pass" with the string "sonata" inside

2. To avoid setting password credentials, use the private key pair (eg, "~/.ssh/YOUR-KEY.pem") of the public key you have used when creating the VM
NOTE: actually, it assumes the default cloud image Username ('ubuntu' or 'centos') using key based authentication

3. Create the hidden file that contains the available Openstack clouds that you can connect [os_client_config](http://docs.openstack.org/developer/os-client-config/) - choose one of the following options:

 $ vi ~/.config/openstack/clouds.yaml

 $ sudo vi /etc/openstack/clouds.yaml

Example for Openstack Mitaka release:

 clouds:
 
   os_alabs_demo:
     auth:
       auth_url: 'http://YOUR_OS_URL:5000/v3'
       username: 'YOUR_OS_USER'
       password: 'YOUR_OS_PASS'
       project_name: 'YOUR_OS_PROJ'
       project_domain_name: "default"
       user_domain_name: "default"
     auth_type: password
     identity_api_version: "3"
     region_name: RegionOne

#### Deployment

 $ git clone -b v2 https://github.com/sonata-nfv/son-install.git

 $ cd son-install

s $* ansible-playbook son-cmud.yml -e "ops=[CREATE/MANAGE/UPGRADE/DESTROY] plat=[SP] pop=[NCSRD|ALABS] distro=[trusty|xenial|Core] ver=[latest|dev|2.1]"

NOTE: depending on the performance of your infrastructure deployment and the download time to get package updates, this run could spent from 30 to 60 minutes.

[![asciicast](http://asciinema.org/a/32wmaiey5d54d5l6msdd7nu32.png)](http://asciinema.org/a/32wmaiey5d54d5l6msdd7nu32?autoplay=1)


#### Example to CREATE a new SONATA Service Platform from the scratch

To deploy the latest SP version running on top of CentOS 7, to the Demo tenant on Altice Labs Openstack VIM: 
 $ ansible-playbook son-cmud.yml -e 'ops=create plat=sp pop=alabs proj=demo distro=Core sp_ver=latest'


### Example to MANAGE the life-cycle of a platform

To stop ALL the services at the SP platform
 $ ansible-playbook son-cmud.yml -e 'ops=manage plat=sp pop=alabs proj=demo distro=xenial action=stop svc=all'

To ask for the status of all the SP services
 $ ansible-playbook son-cmud.yml -e 'ops=manage plat=sp pop=alabs proj=demo distro=xenial action=status svc=all'


### Example to UPGRADE a platform (to be enhanced on future release)

To upgrade the SP (this implementation is on the roadmap)
 $ ansible-playbook son-cmud.yml -e 'ops=upgrade plat=sp pop=alabs proj=demo sp_ver=2.1'


### Example to DESTROY a platform

To terminate a SP platform
 $ ansible-playbook son-cmud.yml -e 'ops=destroy plat=sp pop=alabs proj=demo'


### Dependencies

To deploy infrastrucutre resources to an Openstack VIM, the [Openstack command line clients](http://docs.openstack.org/user-guide/common/cli-install-openstack-command-line-clients.html) must be locally installed (already included in the 'son-cmud.yml' playbook)


## Lead Developers

The following developers are responsible for this repository and have admin rights.

* Alberto Rocha (arocha7)
* Felipe Vicens (felipevicens)
* Navdeep Uniyal (navdeepuniyal)


## Contributing

To contribute to the development of the SONATA gui you have to fork the repository, commit new code and create pull requests.


## License

'son-install' is published under Apache 2.0 license. Please see the LICENSE file for more details.
