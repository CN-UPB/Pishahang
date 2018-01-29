Role Name
=========

This 'rabbitmq' role deploys a RabbitMQ server to a RHEL/CentOS/OEL machine.
It follows the guide RabbitMQ install guide "Installing on RPM-based Linux"
https://www.rabbitmq.com/install-rpm.html

Requirements
------------

RabbitMQ needs Erlang previouslly installed

Role Variables
--------------

- defaults/main.yml - 
- vars/main.yml - 
- global scope (ie. hostvars, group vars, etc.) - 

Dependencies
------------

Before apply the 'rabbitmq' role, it is always a good practice to previouslly upgrade packages on the target machine, by running a playbook that calls  the 'common' role

Example Playbook
----------------

To run the 'rabbitmq' playbook, just run:
$ ansible-playbook deploy-rabbitmq.yml -e target='servername' -vvvv

License
-------

BSD

Author Information
------------------

arocha@ptinovacao.pt
