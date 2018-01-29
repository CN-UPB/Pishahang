Role Name
=========

'pgsql' role installs PostgreSQL on multiple distros 
* CentOS 7 - as steps described here: https://wiki.postgresql.org/wiki/YUM_Installation
* Ubuntu 14.04 
* Ubuntu 16.04 


Requirements
------------

* Requires Ansible 2.2 because of managed services with 'systemd' 
* 'firewalld'


Role Variables
--------------
To install a different pgSQL version, change variable "tarball". 
To set your own dbname, username and passwd, change it at role 'vars'
Current version is: "9.6"


Dependencies
------------
Previous install 
* Python module "psycopg2"


Example Playbook
----------------
Usage:
$ ansible-playbook deploy-pgsql.yml -e target=localhost
$ ansible-playbook destroy-pgsql.yml -e target=localhost


License
-------


Author Information
------------------
"Alberto Rocha", arocha@ptinovacao.pt
