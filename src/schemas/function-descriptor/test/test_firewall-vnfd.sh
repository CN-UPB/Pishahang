#!/bin/bash

##
## Tests the simplest-example package descriptor against
## the package descriptor schema.
##
## Since simplest-example does not contain a '$schema' key
## it is only tested against the standard JSON Schema 
## schema by default. To test it agains our package
## descriptor schema, we need this test.
##

CMD=/home/jenkins/bin/son-validate
BASE_DIR=`dirname $0`
SCHEMA=${BASE_DIR}/../vnfd-schema.yml
FILE=${BASE_DIR}/../examples/firewall-vnfd.yml

#
# We can provide an argument that overrides
# the given CMD variable.
#
if [ $# -eq 1 ]
then
  CMD=$1 
fi

#
# Execute the test.
#
${CMD} -s ${SCHEMA} ${FILE}
