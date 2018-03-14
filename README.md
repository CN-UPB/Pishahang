# Pishahang: Joint Orchestration of Network Function Chains and Distributed Cloud Applications

Pishahang is a managemt and orchestration framework desgined to unify Cloud and NFV infraustructures. It enables complex services compsed of virtual Network Function (NF) and general-purpuse cloud services to be deployed across NFV and Cloud infraustructures.This is provided by consolidating and extending state of the art cloud and NFV tools and technologies.

## Pishahang Architecture

The figure shows the overall architecture of Pishahang.

![Pishahang Architecture](figures/sonata_architecture.png?raw=true)

## Useful Links

* Paper: H. R. Kouchaksaraei, and H. Karl. "Joint Orchestration of Cloud-Based Microservices and Virtual Network Functions."

* Demo Video: https://www.youtube.com/watch?v=vd0vaP8jfNs&t=4s

## Usage

The service platform has only been tested on Ubuntu 16.04, however, if Ansible, Docker and Git are available, other distributions should work as well. This guide uses a clean Ubuntu 16.04 installation.

#### Minimum Requirements

* Memory: 4GB
* Disk: 25GB free space
* A non-root user

### Installation

All commands should be from by the non-root user account.

##### Install packages

```bash
$ sudo apt-get install -y software-properties-common
$ sudo apt-add-repository -y ppa:ansible/ansible
$ sudo apt-get update
$ sudo apt-get install -y git ansible
```

##### Clone repository

```bash
$ git clone https://github.com/tobiasdierich/son-install.git
$ cd son-install
$ echo sonata | tee ~/.ssh/.vault_pass
```

##### Start installation

Replace "\<your\_ip4\_address\>" with the IP address SONATA should be available at.

```bash
$ ansible-playbook utils/deploy/sp.yml -e \
	 "target=localhost public_ip=<your_ip4_address>" -v
```

##### Verify installation

Open your browser and navigate to http://public_ip. Login using the username sonata and password 1234. If the installation was successful, you should now see the dashboard of the service platform.

### Service Deployment

This section will give a step-by-step guide how to deploy a service using the service platform.

##### Connect OpenStack and Kubernetes to SONATA

This step assumes that you have connected to your Kubernetes cluster before using the *kubectl* command line tool.

-   Open your browser and navigate to <http://public_ip>
-   Open the "WIM/VIM Settings" tab
-   Add a new WAN adaptor
    -   Select "Mock" WIM vendor
    -   Enter any WIM name, WIM address, username and password
    -   Confirm by clicking "SAVE"
-   Add OpenStack VIM adaptor
    -   Chose any VIM name
    -   Select the WIM adaptor you just created, enter any country and
        city
    -   Select "Heat" VIM vendor
    -   Fill in the compute and network configuration fields accordingly
-   Add Kubernetes VIM adaptor
    -   Chose any VIM name
    -   Select the WIM adaptor you just created, enter any country and
        city
    -   Select "Kubernetes" VIM vendor
        -   Enter the IP address of the Kubernetes master node
        -   Create a Kubernetes service token with sufficient privileges
            (read & write). An existing service token can be retrieved
            by running the "kubectl describe secret" command.
        -   Copy and paste the cluster’s CA certificate. The certificate
            must be PEM and Base64 encoded. The certificate is usually
            stored in the kubctl config located at `~/.kube/config`
       
##### Enable Kubernetes monitoring

To enable monitoring for a Kubernetes cluster, a new Prometheus scrape
job is needed. The reference config below works for common cluster setups, however, it might need to be adapted
for special Kubernetes setups. Replace the placeholder credentials in
the config with your cluster’s actual credentials. Now, add the scrape
job to Prometheus by POSTing the configuration (transformed to JSON) to
<http://public_ip:9089/prometheus/configuration/jobs>. To verify, open
your browser and navigate to the Prometheus dashboard at
<http://public_ip:9090>. If the metrics list shows entries starting with
*"container"*, the installation was successful.   
 
    
```yaml
- job_name: 'kubernetes-cadvisor'
  scheme: https
  tls_config:
    insecure_skip_verify: true
  basic_auth:
    username: username
    password: password
  kubernetes_sd_configs:
  - role: node
    api_server: https://kubernetes-master
    tls_config:
      insecure_skip_verify: true
    basic_auth:
      username: username
      password: password
  relabel_configs:
  - action: labelmap
    regex: __meta_kubernetes_node_label_(.+)
  - target_label: __address__
    replacement: kubernetes-master:443
  - source_labels: [__meta_kubernetes_node_name]
    regex: (.+)
    target_label: __metrics_path__
    replacement: /api/v1/nodes/${1}/proxy/metrics/cadvisor

```

##### Onboarding Descriptors

Push any descriptors using the corresponding catalogue endpoint:

-   For CSDs: <http://public_ip:4002/catalogues/api/v2/csds>
-   For COSDs:
    <http://public_ip:4002/catalogues/api/v2/complex-services>

Please find example CSDs and COSDs in the `son-examples/complex-services` folder.

##### Deploying a Service

-   Open your browser and navigate to <http://public_ip:25001>
-   Open the "Available Complex Services" tab
-   Click the "Instantiate" button of the service you want to deploy
-   Confirm the instantiate modal (ingress and egress can be empty)

##### Terminating a Service

-   Open your browser and navigate to <http://public_ip:25001>
-   Open the "Running Complex Services" tab
-   Click the "Terminate" button of the service you want to stop

## Lead Developers:

- Hadi Razzaghi Kouchaksaraei (https://github.com/hadik3r)
- Tobias Dierich (https://github.com/tobiasdierich)
