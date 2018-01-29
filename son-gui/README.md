# son-gui  [![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gui)](http://jenkins.sonata-nfv.eu/job/son-gui) 

Gatekeeper GUI designed to cover the needs of the two user groups, service developers and platform administrators in supporting the process of DevOps in SONATA. Gatekeeper GUI is an API management and visualization tool that on one hand enables SONATA developers to manage their services throughout their whole lifecycle, while on the other hand offer Service Platform administrator the ability to provision, monitor and monetize platform resourcess.

## Development
To contribute to the development of the SONATA gui you have to fork the repository, commit new code and create pull requests.

### Dependencies

 * Apache 2 Web Server
 * angular-animate  1.5.5 (MIT)
 * angular-aria 1.5.5 (MIT)
 * angular-cookies 1.5.5 (MIT)
 * angular-messages 1.5.5 (MIT)
 * angular-mocks 1.5.5 (MIT)
 * angular-resource 1.5.5 (MIT)
 * angular-route 1.5.5 (MIT)
 * angular-sanitize 1.5.5 (MIT)
 * angular-touch 1.5.5 (MIT)
 * angular-ui-sortable 0.14.0 (MIT)
 * angular 1.5.5 (MIT)
 * bootstrap 3.3.6 (MIT)
 * jquery-ui 1.11.4 (MIT)
 * jquery 2.2.3 (MIT)
 * grunt 0.4.5 (MIT)


## Installation

Build Docker container image 
```
sudo docker build -t sonata-gui .
```

Run Docker container
```
sudo docker run -d -p 80:80 -e "MON_URL=sp.int2.sonata-nfv.eu:8000" -e "GK_URL=sp.int.sonata-nfv.eu:32001" -e "LOGS_URL=logs.sonata-nfv.eu:12900" sonata-gui
```

## License
SONATA gui is published under Apache 2.0 license. Please see the LICENSE file for more details.


#### Lead Developers
The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

 * Panos Trakadas  		(trakadasp)
 * Panos Karkazis  		(pkarkazis)
 * Manos Zacharioudakis (mzacharioudakis)


#### Feedback-Chanel
* You may use the mailing list sonata-dev@lists.atosresearch.eu
* Please use the GitHub issues to report bugs.
