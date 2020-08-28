FROM python:3.8-slim

# Common dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev git

# Install poetry
RUN pip install poetry

# We do not disable virtual environments for two reasons:
# * `poetry install` messes with system dependencies when --no-dev is set
# * Poetry dependencies would not be separate otherwise

# Using cache directories in docker images is a little ugly, use the project dirs instead
RUN poetry config virtualenvs.in-project true

COPY  schemas/bundled /schemas/bundled
COPY mano-framework/base /mano-framework/base

ENV ENVIRONMENT production
