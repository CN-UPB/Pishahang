FROM pishahang/mano-base

# Configuration
ENV url_gk_api http://son-gtkapi:5000/api/v2/
ENV url_nsr_repository http://son-catalogue-repos:4011/records/nsr/
ENV url_vnfr_repository http://son-catalogue-repos:4011/records/vnfr/
ENV url_monitoring_server http://son-monitor-manager:8000/api/v1/

WORKDIR /mano-framework/plugins/service-lifecycle-manager

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./

CMD ["poetry", "run", "start"]
