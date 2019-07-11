Role Name
=========

Deployment of a MongoDB database

Requirements
------------

Pre-requisites required:
- SELinux python bindings for libselinux

Role Variables
--------------

 defaults/main.yml - 
 vars/main.yml - 
 the global scope (ie. hostvars, group vars, etc.) - 

Dependencies
------------

It's always a good practice to run the 'common' role to have a system with latest packages 

Example Playbook
----------------

To run this playbook: 

$ ansible-playbook deploy-mongo.yml -e "target-guests" -vvvv

License
-------

BSD

Author Information
------------------

arocha@ptinovacao.pt
