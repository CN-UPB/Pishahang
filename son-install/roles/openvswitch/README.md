Role Name
=========

Openvswitch deployment to Ubuntu 16.04 and CentOS 7 machines


Requirements
------------

* Xenial deployment makes use of repo packages (2.5.0)
* Centos 7 deployment makes use of 'tar.gz' tarball and builds the RPM (current LTS version: 2.5.2)


Role Variables
--------------

* to deploy to localhost: pass external variable "target=localhost"
* to deploy to a target machine: create a hosts file like this "target=ovs"

[ovs]
my-ovs ansible_user=centos ansible_ssh_private_key_file=~/.ssh/mykey.pem ansible_host=ipaddr ansible_ssh_common_args='-o StrictHostKeyChecking=no'


Dependencies
------------

Dependencies are handled by the role. Eg, for CentOS 7 the following packages are previously installed:
* libffi-devel,  libtool, graphviz, Cython, iproute, kernel-devel, kernel-debug-devel, autoconf, automake, rpm-build, redhat-rpm-config, python-twisted-core, python-zope-interface, PyQt4, desktop-file-utils, libcap-ng-devel, groff, selinux-policy-devel


Example Playbook
----------------

Example of how to deploy to localhost:

* cd son-install
* ansible-playbook utils/deploy/ovs.yml -e "target=localhost"


License
-------

Apache 2.0

Author Information
------------------

Alberto Rocha, Altice Labs
arocha@ptinovacao.pt
