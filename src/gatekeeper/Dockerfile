FROM pishahang/mano-base

WORKDIR /gatekeeper

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./

EXPOSE 5555

CMD ["poetry", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5555", "gatekeeper.app:app"]
