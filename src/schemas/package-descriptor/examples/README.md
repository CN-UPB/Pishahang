# Examples for the Package Descriptor

Contains some working examples of the package descriptor. Each example should have a corresponding test. Thus, each example is tested with every pull request and we can be sure that all the examples are valid (against the current package descriptor schema).

### Simplest Example

The most simple exampe of a package descriptor can be found in *simplest-example.yml*. It only contains the mandatory fields. Closely related is *simplest-example.son* that is the most simple example of a SONATA package. It only contains the mandatory files i.e. the MANIFEST.MF file in the META-INF directory, and - in addtion - a README.md.

### Sonata Demo Example

The package descriptor of the SONATA demo package can ge found in *sonata-demo.yml*. It contains all the information of the artifacts, such as the NSD, the VNFDs, and the related Docker files, needed for first the SONATA demo. 

#### Sonata Demo Package

The SONATA demo package contains all the information and data needed for the first demo. To this end, it comprises the Network Service Descriptor that constitutes the demo service, comprising the different Virtual Network Functions. Within the package, the NSD can be found at:

 - service_descriptors/sonata-demo.yml

In addition the package contains the Virtual Network Function Descriptors for an iperf VNF, a firewall VNF based on open-vswitch, and a tcpdump VNF. Within the package, the VNFDs can be found at:

 - function_descriptors/iperf-vnfd.yml
 - function_descriptors/firewall-vnfd.yml
 - function_descriptors/tcpdump-vnfd.yml

Each of the VNFs uses a Docker container to actual provide and run the network function. Thus, the package contains the Docker files that define the Docker containers. Within the package, the Docker files are located at:

 - docker_files/iperf/Dockerfile
 - docker_files/firewall/Dockerfile
 - docker_files/tcpdump/Dockerfile

Finally, the packages contains a package descriptor that provides additional information on the structure of the package and the contained data. By definition, the package descriptor is located at:

 - META-INF/MANIFEST.MF
