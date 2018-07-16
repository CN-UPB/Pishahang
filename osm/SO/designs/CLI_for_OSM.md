# [CLI for OSM ](https://osm.etsi.org/gerrit/#/c/165/) #

## Purpose ##
This document describes the functional specification for the CLI for OSM feature. 

## Impacted Modules ##
SO

## Data Model Changes ##
No data model changes are expected as part of this feature.
 
## Overview ##
This feature will add a command line interface to OSM that allows configuration, viewing of operational data and execution of RPCs.

## Feature description ##
Release1 will provide a command line interface(CLI) to access the northbound interface for SO.  The CLI will be model driven and support every config node and  RPCs supported in the OSM data model.

Specifically the following operations will be supported in the CLI.

- Configuration of Various accounts
- Updating NS/VNF descriptor in the catalog( The files specifed in the package updation will not be supported in R1)
- Deleting an NS package from the catalog
- Deleting a VNF package from the catalog
- Launching NS instance with specific parameters (e.g. destination datacentre per VNF, VNF instance name)
- Invoking a service primitive of an NS instance
- Deleting NS instance

In  addition to the above CLI features a script will  be provided that allows on boarding of an NS/VNF package to SO/Launchpad.

The following limitations will exist for release1,

- The SO CLI need to be run from the virtual machine where launchpad is running
- The SO CLI is not meant to be used as the interface to hit the northbound APIs of SO. Any systems (Jenkins automation tests, OSS/BSS) need to use rest APIs to interact with SO.
## Risks ##
None

## Assumptions ##
See limitations in the description section.

