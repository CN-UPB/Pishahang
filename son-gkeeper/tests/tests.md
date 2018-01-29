# Sonata gatekeeper testing scripts

This is the structure of the folder:
```
 root
 └── tests
     ├── checkstyle
     │   └── reports
     ├── integration
     │   └── build
     └── unit
         └── spec
             └── reports
```

* ***Checkstyle*** folder contains the scripts to verify the good style code with rubocop
* ***Integration*** folder contains the scripts to build the containers and perform gatekeeper the integration tests with simple cURL
* ***Unit*** folder containes the script to run the unit tests

## Checkstyle

This is the structure of the checkstyle folder:
``` 
 checkstyle
 ├── gtkall.sh
 ├── <container_name>.sh
 └── reports
```

Inside checkstyle folder, exists a main script that triggers all checkstyle tests. It can be executed from checkstyle folder running the command: `bash gtkall.sh`.

To run a specific checkstyle test, it can be executed from checkstyle folder running the command `bash <name_of_test.sh>`

Once the test are finished, the reports will be available in reports folder.

## Unit tests

This is the structure of the unit folder:
unit
```
├── <container_name>.sh
├── test-dependencies.sh
├── unittest.sh
├── spec
│   └── reports
```
To run the unit test, is required to deploy external containers. The unit folder contains a set of scripts to perform the deployment of external containers and run the unit tests.

Inside the unit folder, exits a script to deploy the test dependencies. It can be executed from unit folder with the command: `bash test-dependencies.sh`

Once the dependencies are running, the unit test can be executed with the command: `bash unittests.sh`

Is it possible to run individual unit test executing the command: `bash <container_name.sh>` from unit folder.

All the reports will be generated inside spec/reports folder

## Integration tess

This is the structure of the integration folder:
```
 integration
 ├── build
 │   ├── build-all.sh
 │   ├── <container_name>.sh>
 ├── deploy.sh
 └── funtionaltests.sh
```

To run the integration test, is required to build and deploy the containers. The integration folder contains a set of scripts to perform these tasks.

Inside the build folder, an script to build all containers is present. It can be execuded from build folder with the command: `bash build-all.sh`

To build a specific container, it can be done from build folder with the command `bash <container_name.sh>`

Once all containers are built, it can be deployed using the deployment script. This script start all dependencies needed to run the son-gatekeeper like databases, catalogues and monitoring for kpis.

To run the functional tests, is needed to have the Gatekeeper running. You can perform the integration tests running the script from integration folder. `bash functionaltest.sh`.
