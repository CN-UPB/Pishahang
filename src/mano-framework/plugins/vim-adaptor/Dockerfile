FROM pishahang/mano-base

WORKDIR /mano-framework/plugins/vim-adaptor

# Install Terraform
RUN apt-get install -y curl unzip
COPY install_terraform.sh ./
RUN ./install_terraform.sh

WORKDIR /mano-framework/plugins/vim-adaptor

# Install dependencies first to speed up successive builds
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . ./

ENV ENVIRONMENT production

CMD ["poetry", "run", "start"]
