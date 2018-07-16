# [Cloud-init Support](https://osm.etsi.org/gerrit/#/c/168/) #

## Purpose ##
This document describes the functional specification for the
cloud-init support feature within the SO Module.

## Impacted Modules ##
SO, RO, VCA

## Data Model Changes ##
The network service descriptor will allow the ability to specify ssh-keys and users,

container nsd-catalog {
  container nsd {
    list key-pair {
      key "name";
      description "Used to configure the list of public keys to be injected as part
                   of ns instantiation";
      leaf name {
        description "Name of this key pair";
        type string;
      }

      leaf key {
        description "Key associated with this key pair";
        type string;
      }
    }
    list user {
      key "name";

      description "List of users to be added through cloud-config";
      leaf name {
        description "Name of the user ";
        type string;
      }
      leaf user-info {
        description "The user name's real name";
        type string;
      }
      leaf passwd {
        description "The user password";
        type string;
      }
    }
  }
}

The ns-instance-config node will be modified to add  the following grouping,

  grouping cloud-config {
    description "List of cloud config parameters";

    list ssh-authorized-key {
      key "key-pair-ref";

      description "List of authorized ssh keys as part of cloud-config";

      leaf key-pair-ref {
        description "A reference to the key pair entry in the global key pair table";
        type leafref {
          path "/nsr:key-pair/nsr:name";
        }
      }
    }
    list user {
      key "name";

      description "List of users to be added through cloud-config";
      leaf name {
        description "Name of the user ";
        type string;
      }
      leaf user-info {
        description "The user name's real name";
        type string;
      }
      leaf passwd {
        description "The user password";
        type string;
      }
    }
  }


A top level node will be introduced in nsr data model that includes the ssh keys. The cloud-config
will  refer to the key-pairs in this list.

  list key-pair {
    key "name";
    description "Used to configure the list of public keys to be injected as part
                 of ns instantiation";
    leaf name {
      description "Name of this key pair";
      type string;
    }

    leaf key {
      description "Key associated with this key pair";
      type string;
    }
  }


## Overview ##
This cloud-init support will add the ability to declaratively specify authorized
ssh keys(user specified and OSM generated) and user name/passwords through cloud-init.

## Feature description ##
Release1 will provide the ability to declaratively specify a list of  authorized
ssh keys and user-name/passwords at the time of Instantiation or in the NS descriptor
which will be passed from UI to SO to RO.

If the keys/user are specified in descriptor, and if they are specified at the time of instantiation
they will be merged  and used for instantiation.

In addition to the user-specified ssh-keys the SO will also generate an
additional "osm ssh keys" which will passed to both RO and VCA.


## Inter-Module Dependencies ##
The RO Module Northbound APIs  need to be enhanced to be able to pass user_data argument and osm key.
SO need to pass the generated OSM keys VCA.

## Risks ##
No significant risks other than the inter-module dependencies.

## Assumptions ##

 - It is assumed that the support for the cloud-init is limited to user-name/password
   and ssh-keys at the NS level and that the same set of keys will be included in all the
   VDUs and all VNFs within the NS. Additional parameters will be added on a need-basis in
   future releases
 - There will not be support to add these keys/user a the VNF level
   The keys/users will be taken as an input at the time of instantiation.
 - Will maintain the support for user-data at the VDU level - If the user-data
   is specified at the VDU level, the inputs from the NS instantiation will be merged
   to the VDU level for  each VDU in the NS.
- There will not be support for these scripts in the NSD.
  It will be handled as an input in ns-instance-config as part of the parameters during instantiation.