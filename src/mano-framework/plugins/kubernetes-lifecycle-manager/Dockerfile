FROM pishahang/mano-base

WORKDIR /mano-framework/plugins/kubernetes-lifecycle-manager

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./

ENV ENVIRONMENT = production

CMD ["poetry", "run", "start"]
