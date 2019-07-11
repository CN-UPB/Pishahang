Role Name
=========

This playbook installs NGINX on CentOS and Ubuntu systems.

Requirements
------------

There are no pre-requirements, besides the initial package upgrade

Role Variables
--------------

- defaults/main.yml
- vars/main.yml 
- global scope variables (ie. hostvars, group vars, etc.) 

Dependencies
------------

The 'common' role can be invoked here to previously upgrade existing packages

Example Playbook
----------------

Usage syntax:

$ ansible-playbook deploy-nginx.yml -e target=localhost
NOTE: the variable "targets" refers the hosts aggregation at the /etc/ansible/hosts inventory file

License
-------

BSD

Author Information
------------------

arocha@ptinovacao.pt
