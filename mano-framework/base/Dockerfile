FROM python:3.8-slim

# Common dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev

# Install poetry
RUN pip install poetry

WORKDIR /mano-framework/base

# We do not disable virtual environments for two reasons:
# * `poetry install` messes with system dependencies when --no-dev is set
# * Poetry dependencies would not be separate otherwise

# Using cache directories in docker images is a little ugly, use the project dirs instead
RUN poetry config virtualenvs.in-project true

COPY . ./

# Common Configuration
ENV broker_host amqp://guest:guest@broker:5672/%2F
ENV broker_exchange son-kernel
ENV mongo_host mongo
ENV mongo_port 27017
