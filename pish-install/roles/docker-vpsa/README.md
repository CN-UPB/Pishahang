Role Name
=========

This role deploys a dockerized version of vPSA Network Service to an existing VM or host. 


Requirements
------------

Docker is automaticaly installed on the guest machine.
Operating System packages are also upgraded before the vPSA deployment.


Role Variables
--------------

* defaults/main.yml 
* vars/main.yml


Dependencies
------------

The vPSA Docker images are available at the public Docker Hub - you can find them here:

* docker search sonatanfv


Example Playbook
----------------

* ansible-playbook utils/deploy/vpsa.yml -e target=localhost


License
-------

Apache 2.0


Author Information
------------------

Alberto Rocha, alberto-m-rocha@alticelabs.com

