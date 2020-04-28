#!/bin/bash

CMD=/home/jenkins/bin/son-validate
BASE_DIR=`dirname $0`
SCHEMA=${BASE_DIR}/test-schema-with-id.yml
FILE=${BASE_DIR}/test_failure.yml

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

#
# Check the return code. Here, we expect the validation
# to fail. Thus, the return code has to be > 0. In that
# case, we have to return 0, such that Jenkins gets the
# right impression of the test.
#
if [ $? -gt 0 ]
then
  exit 0
else
  exit 1
fi
