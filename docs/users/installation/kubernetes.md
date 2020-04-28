# Kubernetes Installation

### Requirements

* Ubuntu 16.04
* At least a network interface with internet connectivity
* At least 2 cores (or more, depending on the number of Containers)
* 2 GB RAM (or more, depending on the number of Containers)
* 20 GB Disk


### Step 1: Prerequisites

```console
$ sudo -s
$ apt-get update
$ apt-get install -y docker.io
$ apt-get update && apt-get install -y apt-transport-https curl
$ curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
$ cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
$ apt-get update
$ apt-get install -qy kubelet=1.15.3-00 kubeadm=1.15.3-00 kubectl=1.15.3-00
$ apt-mark hold kubelet kubeadm kubectl
$ exit
```

### Step 2: Install Kubernetes

```console
$ sudo swapoff -a
$ sudo sed -i '/ swap / s/^/#/' /etc/fstab
$ sudo kubeadm init --apiserver-bind-port 443
## This can take 10+ minutes
```

To allow running ``kubectl`` as non-``root`` user switch to that user and run:

```console
$ mkdir -p $HOME/.kube
$ sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
$ sudo chown $(id -u):$(id -g) $HOME/.kube/config
$ export KUBECONFIG=$HOME/.kube/config
```

### Step 3: Allow spawning of Pods on the master node

To enable spawning Pods on (this) master node:

```console
$ kubectl taint nodes --all node-role.kubernetes.io/master-
```


### Step 4: Install Kubernetes Metrics Server - it is used to retrieved monitoring data.

```console
$ git clone https://github.com/kubernetes-incubator/metrics-server.git
$ cd metrics-server
$ kubectl create -f deploy/1.8+/
$ cd
```

### Step 5: Install and configure networking

Install Pod Network Add-On ``Weave Net``:

```console
$ sudo sysctl net.bridge.bridge-nf-call-iptables=1
$ kubectl apply -f "https://cloud.weave.works/k8s/net?\
k8s-version=$(kubectl version | base64 | tr -d '\n')"
```

Install ``MetalLB``: it exposes Pods to the outside world (e.g., reachability from other VMs in the chain) by assigning an IP address to each ``Service`` with ``type = 'LoadBalancer'``.

```console
$ kubectl apply -f https://raw.githubusercontent.com/\
google/metallb/v0.7.3/manifests/metallb.yaml
```

``MetalLB`` needs additional information, like which pool of IP addresses to use and assign to ``Services``.
To configure that please refer to [this](https://metallb.universe.tf/configuration/) webpage.

### Step 6: Install Kubernetes dashboard

Run the following command. "dashboard.yaml" can be found [here](https://github.com/CN-UPB/Pishahang/blob/master/osm/documentation/kubernetes-files/dashboard.yaml)

```console
$ kubectl apply -f dashboard.yaml
```
The dashboard can be accessed on this link: ``https://<master-ip>:<port>`` . "master-ip" is the IP address of the k8 host and "port" can be retrieved by running the following command
```console
$ kubectl -n kube-system get service kubernetes-dashboard
```
An example result is like the following:

```console
NAME                   TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)         AGE
kubernetes-dashboard   NodePort   10.110.204.212   <none>        443:31429/TCP   23h

``` 
In this example, the port number that should be used is `31429`.

To login to the dashboard, you need a token which can be retrieved by running the following command.
```console
$ kubectl describe secret
```
To have full access to the dashboard run the following command. "access.yaml" can be found [here](https://github.com/CN-UPB/Pishahang/blob/master/osm/documentation/kubernetes-files/access.yaml)
```console
$ kubectl apply -f access.yaml
```