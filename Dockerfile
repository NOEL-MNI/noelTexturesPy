FROM noelmni/antspynet:master-58b19c9-mamba AS builder
LABEL maintainer=<ravnoor@gmail.com>

# set variable for conditional test execution
ARG SKIP_TESTS=false

USER root

# Enable Dash end-to-end tests inside Docker (headless Chromium)
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    ca-certificates \
    fonts-liberation && \
  rm -rf /var/lib/apt/lists/*

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.docker.yml environment.yml
RUN echo "installing environment" && \
  micromamba clean --all --yes && \
  micromamba install --name base --file environment.yml --yes && \
  micromamba clean --all --yes

WORKDIR /usr/local/src

COPY . .
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-deps dist/*.whl

# Install Dash testing extras for dash.testing (Selenium fixtures)
RUN pip install "dash[testing]>=3.3,<4"

# run tests if SKIP_TESTS is not true
RUN if [ "${SKIP_TESTS}" != "true" ]; then bash tests/run_tests.sh; fi

# production image
FROM mambaorg/micromamba:2-debian12-slim
ENV TZ=America/Montreal
COPY --from=builder /opt/conda /opt/conda
COPY --from=builder /usr/local/src/templates /usr/local/src/templates
USER $MAMBA_USER

WORKDIR /usr/local/src

EXPOSE 9999

ARG MAMBA_DOCKERFILE_ACTIVATE=1
SHELL [ "/usr/local/bin/_dockerfile_shell.sh" ]
ENTRYPOINT [ "/usr/local/bin/_entrypoint.sh", "textures_app" ]
