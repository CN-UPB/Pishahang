Role Name
=========

A basic role to deploy Odoo (formerly OpenERP).

This role is based on "packaged installers" method provided at: https://www.odoo.com/documentation/10.0/setup/install.html


Requirements
------------

The assembled Odoo package also installs PostgreSQL 9.3 


Role Variables
--------------

The current configuration installs version '10.0': to install a different version, change {{ tarball }} at group vars


Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.


Example Playbook
----------------


$ ansible-playbook deploy-odoo.yml  -e target=localhost
$ ansible-playbook destroy-odoo.yml -e target=localhost


License
-------


Author Information
------------------

<Alberto Rocha> arocha@ptinovacao.pt
