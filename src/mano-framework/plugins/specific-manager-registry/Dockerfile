FROM pishahang/mano-base

# configrurations

# the id of docker network
ENV network_id sonata

# broker management host; used for creating vhost, user, and setting permissions
ENV broker_man_host http://son-broker:15672

# specific management vhost; used for communcation between SSMs/FSMs and MANO plugins(SMR,SLM,FLM,Executives)
ENV sm_broker_host amqp://specific-management:sonata@son-broker:5672

#docker host
ENV DOCKER_HOST unix://var/run/docker.sock


WORKDIR /mano-framework/plugins/specific-manager-registry

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./

CMD ["poetry", "run", "specific-manager-registry"]
