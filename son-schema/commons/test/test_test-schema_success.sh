#!/bin/bash

CMD=/home/jenkins/bin/son-validate
BASE_DIR=`dirname $0`
SCHEMA=${BASE_DIR}/test-schema.yml
FILE=${BASE_DIR}/test_success.yml

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
