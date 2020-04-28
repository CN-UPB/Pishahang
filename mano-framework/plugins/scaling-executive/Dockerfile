FROM pishahang/mano-base

# Configuration
ENV sm_broker_host amqp://specific-management:sonata@son-broker:5672

WORKDIR /mano-framework/plugins/scaling-executive

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./
RUN poetry install --no-dev --no-interaction

CMD ["poetry", "run", "start"]
