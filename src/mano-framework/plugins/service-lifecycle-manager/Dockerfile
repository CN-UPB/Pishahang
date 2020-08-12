FROM pishahang/mano-base

# Configuration
ENV url_monitoring_server http://son-monitor-manager:8000/api/v1/

WORKDIR /mano-framework/plugins/service-lifecycle-manager

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./

CMD ["poetry", "run", "start"]
