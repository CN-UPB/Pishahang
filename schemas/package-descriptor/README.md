# Package Descriptor + Schema
The package descriptor file specifies the content, artifacts, and dependencies of a SONATA package. The corresponding schema file specifies the structure of the package descriptor. It makes sure the relevant information is provided to parse the package in a meaningful way. It can be used to validate the package descriptor file.

In a package, the package descriptor file MUST be placed in the ***META-INF*** directory in the root of the package. Moreover, it MUST be named ***MANIFEST.MF***. Please note that, dependent on the operating system, directory and file names are case sensitive.

## Sections of the Package Descriptor

Below we discuss the various section of a package descriptor. The general descriptor section contains some of the manditory fields that have to be present in each and every package descriptor. All other sections are optional.

#### General Descriptor Section

On the root level, the general descriptor section contains the mandatory fields required in the package descriptor. 

- **descriptor_version** identifies the version of the package descriptor schema that is used to specify the file structure.
- **$schema** (optional) provides a link to the schema that is used to specify the file structure and can be used to validate the package descriptor file. This is related to the original JSON schema specification.

Moreover, the package signatur, i.e. the *package_group*, the *package_name*, and the *package_version*, is of great importance, as it identifies the package uniquely.

Best practicies for creating the signatur can be derived from the Java Maven naming conventions for groupId, artifactId, and version. To this end, the *package_group*, the *package_name*, and the *package_version* should be named as follows:

- **vendor** will identify the package uniquely across all packages. It should at least be comprised of the reverse domain name that is under your controll. Moreover, it might have as many sub-groups as needed. For example: eu.sonata-nfv.nec.
- **name** is the name of the package without its version. It can be created with any name written in lower letters and no strange symbols.
- **version** names the version of the package. Any typical version with numbers and dots, such as 1.0, 1.1, and 1.0.1 is allows here. The package version must be increased with any new (changed) instance of the service.

The general descriptor section also contains some optional components as outlined below.


- **maintainer** (optional) describes the maintainer of the package, like *John Doe, NEC*.
- **description** (optional) provides an arbitrary description of the package.
- **md5** (optiona) provides an MD5 hash over the package content, i.e. all files contained in the package EXCEPT the package descriptor, i.e. /META-INF/MANIFEST.MF, as this file contains this hash.
- **signature** (optional) provides a cryptographic signature over the package content, i.e. all files contained in the package EXCEPT the package descriptor, i.e. /META-INF/MANIFEST.MF. Thus, a package customer can verify the integrity and the origin of the package.
- **entry_service_template** (optional) specifies THE service template of this package. In General the package can contain more than one network service descriptor as dependencies. In order to identify the descriptor that describes the service of this package, it has to be named here.
- **sealed** (optional) is a boolean value that states wheter this package is self-contained, i.e. it already contains all its relevant artifacts (true), or it has external dependencies that may have to be provided from somewhere else. Default is *false*.

#### Package Content Section

The package content section contains all the artifacts that are contained and shipped by the package. The section is optional and starts with:

- **package_content** (optional) holds an array of artifacts contained in the package

While the parent section is optional, once it is specified it has to have at least one item with the following information:

- **name** specifies the path to the resource in the package.
- **content_type** specifies the type of content, like *application/vnd.sonata.service_template*
- **md5** (optional) specifies an MD5 hash of the resource.
- **sealed** (optional) overrides the default *sealed* value specified in the general descriptor section on a per-artifact basis.

#### Package Resolver Section

The package resolver sections contains information about catalogs and repositories needed to resolve the dependencies specified in this package descriptor. This information might be used in addition to the default catalogs and repositories configured already on the service platform (or the SDK). The section is optional and starts with:

- **package_resolvers** (optional) holds an array of catalogs used to resolve dependencies and download additional packages.
 
While the parent section is optional, once it is specified it has to have at least one item with the following information:

- **name** specifies the path to the catalog.
- **credentials** (optional) provides the credentials that might be needed to access the catalog.

#### Package Dependencies Section

In the package dependencies section, one can specify additional packages this package depends up on. The packages are automatically downloaded from the various catalogs provided either by default from the service platform or as configured in the *package resolver section*. The section is optional and starts with:

- **package_dependencies** (optional) holds an array of packages this packages depends up on.

While the parent section is optional, once it is specified it has to have at least one item with the following information:

- **name** specifies the name of the package, similar to the name of this package.
- **group** specifies the name of the group, similar to the group name of this package.
- **version** specifies the version or version ranges of the package that is needed. For example one can specify the exact version like, *1.0.1-beta*, but also ranges such as *>= 1.0*, *<= 1.0*, even in combination with boolean expression *>= 1.0 && < 2.0*, *1.1 || 1.2*, etc.
- **credentials** (optional) provides the credentials that might be needed to *use* this package.
- **verification_key** provides the public key of the package maintainer to verify the package.

#### Artifact Dependencies Section

- **artifact_dependencies** (optional)
 
While the parent section is optional, once it is specified it has to have at least one item with the following information:

- **name** specifies the name of the artifact to download.
- **url** specifies the URL where to download the package from. Moreover, there needs to be a protocol handler that is able to download the artifact using the given protocol, like HTTP. For now, we only support *HTTP* and *HTTPS*. Thus, the URL has to start with one of these protocols.
- **credentials** (optional) provides the credentials that might be needed to download the artifact.


## Example

A simple example of a package descriptor.


```
---
descriptor_version: "1.0"

package_group: "eu.sonata.nfv"
package_name: "example-package"
package_version: "1.1"
package_maintainer: "Michael Bredel, NEC Labs Europe"
package_description: > 
  "My first package descriptor"

entry_service_template: "path/to/entry-service-description"
sealed: true

package_content:
 - name: "/path/to/descriptor"
   content-type: "application/sonata.service_descriptor"
   md5: "00236a2ae558018ed13b5222ef1bd9f3"
   sealed: false
 - name: "/path/to/descriptor"
   content-type: "application/sonata.service_descriptor"
   sealed: true
 - name: "/path/to/vm-image"
   content-type: "application/sonata.image"

package_resolvers:
  - name: "http://www.bredel-it.de/path/to/catalog"
    credentials: "my (optional) credentials"

package_dependencies:
 - name: "my-dependent-package"
   group: "eu.sonata.nfv"
   version: "1.0"
   credentials: "my (optional) credentials"

artifact_dependencies:
  - name: "my-vm-image"
    url: "http://www.bredel-it.de/path/to/vm-image"
    md5: "00236a2ae558018ed13b5222ef1bd9f3"
    credentials: "my (optional) credentials"
```
