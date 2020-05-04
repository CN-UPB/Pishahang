#!/usr/bin/env bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

echo "$dir"

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting SLM.."

# Stop Original SLM and start pishahang changes 
touch plugins/son-mano-service-lifecycle-management/_test.py
rm plugins/son-mano-service-lifecycle-management/_test.py

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting Policy Plugin.."
touch plugins/son-mano-mv-policy/_test.py
rm plugins/son-mano-mv-policy/_test.py

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting Forecast Plugin.."
touch plugins/son-mano-traffic-forecast/_test.py
rm plugins/son-mano-traffic-forecast/_test.py

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting MV Plugin.."

touch plugins/son-mano-mv/_test.py
rm plugins/son-mano-mv/_test.py
