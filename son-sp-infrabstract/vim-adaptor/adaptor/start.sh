echo "Running plugin installer"

mvn -e -q compile assembly:single;

/docker-entrypoint.sh

/test.sh

