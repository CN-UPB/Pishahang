Deploy Docker engine through Ansible

Target machines running:
- Ubuntu 14.04 (Trusty)
- Ubuntu 16.04 (Xenial)
- CentOS 6
- CentOS 7 

Usage syntax:

$ ansible-playbook deploy-docker.yml -e target='yourInventoryHostsAggregation'

Validation using an ad-hoc command:

$ ansible <yourInventoryHostsAggregation> -m command -a 'docker images'
