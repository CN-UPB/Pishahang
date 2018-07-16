# [MultiSite-NSD Support](https://osm.etsi.org/gerrit/#/c/160/) #

## Purpose ##
This document describes the functional specification for the
SO module for multi site Network Service that involves supporting NS instances with VNFs running
in different datacenters.

## Impacted Modules ##
SO, RO, UI

## Data Model Changes ##

The ns-instance-config node will be modified to add  the following list to specify vim-account 
for vnfs. If cloud account and datacenter name is not provided for individual VNF than 
ns-instance-config level datacenter name will be used for all VNFs if provided or for those where 
below mapping is not provided.

    list vnf-cloud-account-map {
      description
          "Mapping VNF to Cloud Account where VNF will be instantiated";

      key "vnfd-id-ref";
      leaf vnfd-id-ref {
        description
            "A reference to a vnfd. This is a
            leafref to path:
            ../../../../nsd:constituent-vnfd
            + [nsr:id = current()/../nsd:id-ref]
           + /nsd:vnfd-id-ref";
        type yang:uuid;
      }

      leaf cloud-account {
        description
            "The configured cloud account where VNF is instantiated within.
            All VDU's, Virtual Links, and provider networks will be requested
            using the cloud-account's associated CAL instance";
        type leafref {
          path "/rw-cloud:cloud/rw-cloud:account/rw-cloud:name";
        }
      }

      leaf om-datacenter {
        description
            "Openmano datacenter name to use when instantiating
            the VNF.";
        type string;
      }
    }

Constituent VNFR in NSR will be augemented to include datacenter name for individual VNF.

  augment /nsr:ns-instance-opdata/nsr:nsr/nsr:constituent-vnfr-ref {
    leaf cloud-account {
      description
        "The configured cloud account in which the VNF is instantiated within.
         All VDU's, Virtual Links, and provider networks will be requested
         using the cloud-account's associated CAL instance";
      type leafref {
        path "/rw-cloud:cloud/rw-cloud:account/rw-cloud:name";
      }
    }
    leaf om-datacenter {
      description
        "Openmano datacenter name to use when instantiating
         the network service.";
      type string;
   }
  }

VLR in NSR will be augemented to include datacenter name. Virtual link will be created in each of 
cloud account where constiuent VNFs are instantiated.

  augment /nsr:ns-instance-opdata/nsr:nsr/nsr:vlr {
    leaf cloud-account {
      description
        "The configured cloud account in which the VL is instantiated within.";
      type leafref {
        path "/rw-cloud:cloud/rw-cloud:account/rw-cloud:name";
      }
    }
    leaf om-datacenter {
      description
        "Openmano datacenter name to use when instantiating
         the network service.";
      type string;
    }
  }

VNFR will now have new field indicating datacenter where VNF instance is started.

    leaf om-datacenter {
      description
          "Openmano datacenter name to use when instantiating
          the network service.";
      type string;
    }

VLD will now have a new field vim-network-name to indicate pre-created network name to be
used for this Virtual link. Release 0 provider-network in the VLD was used for this and
this will be changed to use vim-network-name. VLR name will use the vim-network-name if present.

      leaf vim-network-name {
        description
            "Name of network in VIM account. This is used to indicate
            pre-provisioned network name in cloud account.";
        type string;
      }


## Overview ##

Current implementation in Release 0 allowed the deployment of a Network Service instance
 in the datacenter chosen by the user. Specifically the MWC demo covered 4 deployments 
and the user decided for every deployment the datacenter where to deploy.
However, it is not possible to span an NS instance across different datacenters on a 
single scenario with Release 0(e.g. with some VNFs running in datacenter A and others in 
datacenter B).

There are several use cases where a multi-site NS applies, e.g.:
- The deployment of a full core network with several PEs in different datacenters.
- The deployment of VoIP network where some elements are centralized in a datacenter while others 
  are distributed (e.g. SBC).

Relase1 will support NS instances with VNFs running in different datacenters.

## Feature description ##

To support running NS instances with VNFs running in different datacenters, UI will support
indicating both the Cloud Account and the Datacenter for each VNF during NS instantiation. This 
will be implemented with addition of Cloud account and Datacenter name for each VNF during NS 
instantiation as indicated in Data model section.
The cloud account and datacenter name where VNF needs to be instantiated will be populated in both 
NSR consituent-vnfs and VNFR and same will be sent to RO as part of instance scenario create.

It is assumed that network interconnecting datacenter is pre-provisioned and has connection
to connect two datacenter sites through this network.Also each Virtual link in NSD 
will map to Openamno NSD connections node. It is assumed that RO is expected to reuse 
pre-provisioned network in each of applicable cloud accounts or create new networks in applicable 
cloud account. Openmano NSD connection node will have type external network and refer to 
vim-network-name as Openmano network name and passed in NSD from SO to RO.

## Inter-Module Dependencies ##
The RO Module Northbound APIs  need to be enhanced to allow specifying datacenter where individual 
VNFs should be instantiated.  SO need to pass the datacenter name for VNFs to RO.

## Risks ##
RO API definitions are critical to complete the integration of the feature with RO.

## Open Item ##
Northbound RO API changes to indicate datacenter for individual VNFs.

## Assumptions ##

 - It is assumed that the networks interconnecting several datacenters are pre-preprovisioned 
   ie, there is an E-LAN/E-LINE connection established between the sites for the provider networks
   on each location to connect to each other.
 - It is also expected that same name is used for these networks connecting sites with each other in Openmano so that
   virtual link can use vim-network-name applicable in multiple datacenter networks.
 - The datacenter for individual VNFs will be handled as an input in ns-instance-config as part of 
   the parameters during instantiation.
 - There is no change to way networks are exposed by RO ie existing VNFD/NSD Openmano Descriptors 
   will be used.
 - VCA is not functionally impacted.

