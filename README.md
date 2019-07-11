# Pishahang: Joint Orchestration of Network Function Chains and Distributed Cloud Applications

Pishahang is a framework consolidated from state-of-the-art NFV and Cloud management and orchestration tools and
technologies to provide orchestration for services deployed across multiple technological domains.

## Useful Links

### Papers: 
* H. R. Kouchaksaraei, T. Dierich and H. Karl, [Pishahang: Joint Orchestration of Network Function Chains and Distributed Cloud Applications](http://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8460134&isnumber=8458492), 2018 4th IEEE Conference on Network Softwarization and Workshops (NetSoft), Montreal, QC, 2018, pp. 344-346. DOI: 10.1109/NETSOFT.2018.8460134

* H. R. Kouchaksaraei and H. Karl. 2019. [Service Function Chaining Across OpenStack and Kubernetes Domains](https://dl.acm.org/citation.cfm?id=3332505). In Proceedings of the 13th ACM International Conference on Distributed and Event-based Systems (DEBS '19). ACM, New York, NY, USA, 240-243. DOI: https://doi.org/10.1145/3328905.3332505

### Demo videos:
* Service deployment: https://www.youtube.com/watch?v=vd0vaP8jfNs&t=4s

* Service chaining support: https://www.youtube.com/watch?v=zCci3-2gU44&t=22s

## Usage

Please refer to [this](https://github.com/CN-UPB/Pishahang/wiki) wikipage for installing Pishahang, Devstack, and Kubernetes. 


### Service Deployment

This section will give a step-by-step guide how to deploy a service using the service platform.

##### Connect OpenStack and Kubernetes to Pishahang

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
- Marvin Illian (https://github.com/OrangeOnBlack)

