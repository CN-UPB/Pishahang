***********************
Kubernetes Installation
***********************

This guide describes the installation of MicroK8s, an easy-to-setup single-node Kubernetes deployment for development purposes.

.. note::
    If you need a production Kubernetes setup, please refer to the official Kubernetes documentation for installation instructions.
    In this case, the services that are shipped with MicroK8s have to be setup manually.


Requirements
============

* Ubuntu >= 18.04
* At least one network interface with internet connectivity
* At least 2 cores (or more, depending on the number of Containers)
* 4 GB RAM (or more, depending on the number of Containers)
* 20 GB Disk


Install Docker and Kubernetes
=============================

.. code-block:: bash

    sudo apt install -y curl snapd
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo snap install microk8s --classic --channel=1.18/stable


To allow kubernetes commands that require root access to be run without sudo, run

.. code-block:: bash

    sudo usermod -a -G microk8s $USER
    sudo chown -f -R $USER ~/.kube
    su - $USER


Add your domain to the CA cert's alt names
==========================================

If you would like to be able to access the dashboard and the API via your machine's domain name in addition to its IP, add ``DNS.6 = <your domain name>`` in the ``alt_names`` sections of the csr configuration file:

.. code-block:: bash

    nano /var/snap/microk8s/current/certs/csr.conf.template


Enable addons
=============

.. code-block:: bash

    microk8s enable dashboard dns metrics-server metallb


The above command will enable the listed addons and prompt for a ``MetalLB`` address range.
``MetalLB`` is used to expose Pods to the outside world by assigning an IP address to each ``Service`` with ``type = 'LoadBalancer'``.
These IP addresses will be chosen from the address range that you provide in this step.


Expose the dashboard
====================

To expose the dashboard to the outside of the machine that runs Kubernetes, set the type of the dashboard service to ``NodePort`` by editing the service with

.. code-block:: bash

    EDITOR=nano microk8s kubectl -n kube-system edit service kubernetes-dashboard

At the bottom of the file, change ``type: ClusterIP`` to ``type: NodePort`` and save the file.

The dashboard can then be accessed at ``https://<host>:<port>`` where ``host`` is the IP address or domain name of the host that runs Kubernetes and ``port`` can be retrieved by running

.. code-block:: bash

    microk8s kubectl -n kube-system get service kubernetes-dashboard

An example result looks like this:

.. code-block:: console

    $ microk8s kubectl -n kube-system get service kubernetes-dashboard
    NAME                   TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)         AGE
    kubernetes-dashboard   NodePort   10.110.204.212   <none>        443:30201/TCP   10m

In this example, the public port number of the dashboard service is ``30201``.

To login to the dashboard, you need a token which can be retrieved by running

.. code-block:: bash

    token=$(microk8s kubectl -n kube-system get secret | grep default-token | cut -d " " -f1)
    microk8s kubectl -n kube-system describe secret $token
