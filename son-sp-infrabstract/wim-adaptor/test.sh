#!/bin/bash
set -e
echo "Setting environment"
/setenv.sh

echo "Doing maven test"
cd /adaptor
mvn -q -Dcheckstyle.config.location=google_checks.xml checkstyle:checkstyle findbugs:findbugs cobertura:cobertura
