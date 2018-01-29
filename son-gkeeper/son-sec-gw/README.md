# [SONATA](http://www.sonata-nfv.eu)'s Gatekeeper API micro-service
[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gkeeper)](http://jenkins.sonata-nfv.eu/job/son-gkeeper)

This folder has the configuration, code and specifications of sonata security gateway.

## Architecture
The son-sec-gw will enable a security layer for SONATA Service Platform components. To be used as a part of infrastructure the following was considered:
* Is a nginx proxy-pass container.
* Is located on front of son-gktapi and son-gui. 
* The certificates should be mounted as volume inside the son-sec-gw
* The communication between son-sec-gw and internal components is always https
* The communication between clients and son-sec-gw is https if certificates exists, otherwise http is allowed but with a warning.

```

              +----------------+                +---------------+
     https    |                |     http       |               |
   +---------^+  son-sec-gw    +---------------->  son-gtk-api  |
              |                |        |       |               |
              +----------------+        |       +---------------+
                                        |
                                        |       +---------------+
                                        |       |               |
                                        +------->    son-gui    |
                                                |               |
                                                +---------------+
```

## Usage
To use this module you can do it by this way:

```sh
$ docker run --name son-sec-gw -d -p 80:80 -p 443:443 -v /etc/ssl/private/sonata/:/etc/nginx/cert/ --link son-gtkapi --link son-gui sonatanfv/son-sec-gw 

```

OPTIONS:
* --name = Container name (Optional).
* --link = Link with son-gtkapi and son-gui containers.
* -p = 80:80 External port 80 -> Internal port 80 and 443:443 External port 443 -> Internal port 443.
* -v = The certificates have to be located in the folder /etc/nginx/cert with the names CERT=sonata.cert KEY=sonata.key.
