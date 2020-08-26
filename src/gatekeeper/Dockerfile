FROM pishahang/mano-base

WORKDIR /gatekeeper

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./

EXPOSE 5555

CMD ["poetry", "run", "gunicorn", "--worker-tmp-dir=/dev/shm", "--workers=2", "--threads=4", "--worker-class=gthread", "-b", "0.0.0.0:5555", "gatekeeper.app:app"]
