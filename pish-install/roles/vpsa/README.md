Role Name
=========

The 'virtual Security Appliance' (vSA) role deploys a platform running 3 services:
* HAProxy - for network load balancing
* Squid - for caching content
* Snort - for intrusion detaction system

Requirements
------------

Current version, retieves public Docker images from Hub


Role Variables
--------------


Dependencies
------------


Example Playbook
----------------

* ansible-playbook son-cmud.yml -e "ops=create environ=vpsa pop=alabs distro=xenial"

'son-cmud' variables are set herei (change to the 'key=value' that fits to your environment):
* environments/vpsa/group_vars


License
-------

Apache 2.0

Author Information
------------------

Alberto Rocha, arocha@ptinovacao.pt
