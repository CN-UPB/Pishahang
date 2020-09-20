FROM pishahang/mano-base

WORKDIR /mano-framework/plugins/placement

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./

CMD ["poetry", "run", "start"]
