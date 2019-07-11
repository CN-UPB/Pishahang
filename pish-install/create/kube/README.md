## Deployment of a Kubernetes cluster 

This playbook provides a K8s cluster in 3 steps:

1. provisions 4 VMs:
* 1 Kubernetes Master
* 3 Kubernetes Nodes

2. standardizes the VM's with latest operating system packages, required libraries and tools

3. install Kubernetes componentes, namely:
* Kubernetes Master role
  - etcd
  - controller-manager
  - scheduler
  - api
* Kubernetes Node role
  - Kubebet
  - Docker
  - Proxy


## How to use

* ansible-playbook son-cmud.yml -e "ops=create environ=kube"

NOTE: this playbook implements the manual install process described [here](https://kubernetes.io/docs/getting-started-guides/centos/centos_manual_config/)

