GOAL
====

* deploy a platform made of 2 frontend servers with NGINX and 2 backend servers with PostgreSQL
* also generates the hosts file to be used by the Ansible inventory


INSTALL
=======

* get the "terraform" repo from Github: https://github.com/arocha7/terraform.git


DEPENDENCIES
============

This configuration uses Ansible roles to deploy NGINX and pgSQL

* get the "ansible" repo from Github: https://github.com/arocha7/ansible.git


USAGE
=====

cd terraform/two-layers-platf
terraform plan    -var-file='os_2layers-trusty.tfvars'
terraform apply   -var-file='os_2layers-trusty.tfvars'
terraform destroy -var-file='os_2layers-trusty.tfvars'


FEEDBACK
========

* arocha@ptinovacao.pt

