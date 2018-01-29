Role Name
=========

This playbook deploys a Kubernetes Master. It installs:
* etcd
* kube-apiserver
* kube-controller-manager
* kube-scheduler
* flannel


Requirements
------------


Role Variables
--------------


Dependencies
------------

To use Ansible Cloud module Openstack you will need the following pre-requisites:
* [Openstack command line clients](https://docs.openstack.org/user-guide/common/cli-install-openstack-command-line-clients.html)
* [Shade library](https://pypi.python.org/pypi/shade)

Guides
------
This role was created according to the manual install procces described on the following sources:

* [Kubernetes, User Guide, Creating a Cluster, Running Kubernetes on Custom Solutions, Bare Metal, CentOS](https://kubernetes.io/docs/getting-started-guides/centos/centos_manual_config/)
* [Installing Kubernetes Cluster with 3 minions on CentOS 7 to manage pods and services](https://severalnines.com/blog/installing-kubernetes-cluster-minions-centos7-manage-pods-services)

Example Playbook
----------------

To deploy a Kubernetes cluster run:

* ansible-playbook kube.yml

To deploy a Kubertnetes Master run:

* ansible-playbook kube-master.yml

To deploy a Kubertnetes Node run:

* ansible-playbook kube-nodes.yml

[ASCIINEMA](http://asciinema.org/a/57pdyw66gua5owa8v27vizzbm)

License
-------

BSD

Author Information
------------------

Alberto Rocha, Altice Labs: arocha@ptinovacao.pt
