VIM Adaptor: [![VIM adaptor](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-sp-infrabstract-vim)](http://jenkins.sonata-nfv.eu/job/son-sp-infrabstract-vim)

WIM Adaptor: [![WIM adaptor](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-sp-infrabstract-wim)](http://jenkins.sonata-nfv.eu/job/son-sp-infrabstract-wim)

# son-sp-infrabstract

In the SONATA Service Platform the Infrastructure Abstraction plays the role of an abstraction layer between the MANO framework and the underlying (virtualised) infrastructure.
The Infrastructure Abstraction allows the orchestrator's entities to interact with the infrastructure, regardless of the specific technology used to manage it. It exposes interfaces to manage service and VNF instances, retrieve monitoring information about the infrastructure status, reserve resources for services deployment.
It is composed of two main modules, the Virtual Infrastructure Manager Adaptor (VIM Adaptor) and the WAN infrastructure Manager Adaptor (WAN Adaptor). The VIM Adaptor is responsible for exposing an interface to interact with one or more VIMs, managing computational, network or storage resource in one or more Points of Presence to the Sonata MANO framework . The WIM Adaptor allows the service platform to manage network resources connecting different NFVI-PoPs in a vendor agnostic fashion, in order to provide connectivity to the deployed services.


## Repository Structure
  
 * `VIM Adaptor` contains the sonata Virtual Infrastructure Manager adaptor files.
 * `WIM Adaptor` contains the sonata WAN Infrastructure Manager adaptor files.

## Contributing

Contributing to the son-sp-infrabstract is really easy. You must:

1. Clone [this repository](http://github.com/sonata-nfv/son-sp-infrabstract);
2. Work on your proposed changes, preferably through submiting [issues](https://github.com/sonata-nfv/son-sp-infrabstract/issues);
3. Submit a Pull Request;
4. Follow/answer related [issues](https://github.com/sonata-nfv/son-sp-infrabstract/issues) (see Feedback-Chanel, below).

For more information on VIM Adaptor and WIM Adaptor, please see the README file in the relevant subfolder.

## License

This Software is published under Apache 2.0 license. Please see the LICENSE file for more details.

## Useful Links

* https://www.openstack.org/ the OpenStack project homepage
* https://pypi.python.org/pypi/pip Python Package Index
* https://maven.apache.org/ Java Maven
* https://www.docker.com/ The Docker project
* https://docs.docker.com/compose/ Docker-compose documentation


---
#### Lead Developers

The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

* [Dario Valocchi](https://github.com/DarioValocchi)

#### Feedback-Channel

* You may use the mailing list [sonata-dev@lists.atosresearch.eu](mailto:sonata-dev@lists.atosresearch.eu)
* [GitHub issues](https://github.com/sonata-nfv/son-sp-infrabstract/issues)
