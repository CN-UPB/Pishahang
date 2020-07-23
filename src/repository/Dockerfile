FROM pishahang/mano-base

WORKDIR /repository

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./

ENV ENVIRONMENT=production

CMD ["poetry", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "repository:app_instance"]
