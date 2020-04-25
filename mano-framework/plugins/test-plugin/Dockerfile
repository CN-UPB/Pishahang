FROM pishahang/mano-base

WORKDIR /mano-framework/plugins/test-plugin

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./
RUN poetry install --no-dev --no-interaction

CMD ["poetry", "run", "start"]
