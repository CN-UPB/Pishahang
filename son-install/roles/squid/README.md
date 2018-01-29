Role Name
=========

A role to deploy Squid proxy server to a target CentOS 7, Ubuntu 14.04 and Ubunti 16.04 machine


Requirements
------------

No specific requirements.


Role Variables
--------------

To set a particular configuration that fits your needs, just change the 'roles/squid/files/squid.conf' configuration file - example: <br>

proxy service port:
* http_port 3128

local address space:
* acl alabsintranet 10.112.0.0/16
* acl alabspopnet 172.31.6.0/24
* acl ncsrdpopnet 10.100.32.0/24


Dependencies
------------

* Openstack command line clients
* Shade >=1.16.0


Example Playbook
----------------

Get teh repo
* git clone https://github.com/sonata-nfv/son-security-pilot.git
* cd son-security-pilot/install

To generate an Ubuntu 16.0 VM with Squid 3.5 on an Openstack VIM:
* ansible-playbook son-cmud.yml -e "ops=create plat=squid pop='YOUR_OS_VIM' proj='YOUR_OS_TENANT' distro='YOUR_PREFERED_OPERATING_SYSTEM_DISTRO'"


To install Squid onto the local machine:
* ansible-playbook utils/deploy/squid.yml

To install Squid onto a target machine:
* ansible-playbook utils/deploy/squid.yml [-e target='IP-ADDRESS-OF-THE-GUEST-MACHINE']


License
-------

Apache 2.0


Author Information
------------------

Alberto Rocha, Altice Labs (alberto-m-rocha@alticelabs.pt)
