# supports amd64,arm64,ppc64le
# note: qemu emulated ppc64le build might take ~6 hours

# use micromamba to resolve dependencies cross-platform
FROM mambaorg/micromamba:2-debian12-slim as builder

# install libpng to system for cross-architecture support
# https://github.com/ANTsX/ANTs/issues/1069#issuecomment-681131938
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      apt-transport-https \
      build-essential \
      ca-certificates \
      git \
      libpng-dev

USER $MAMBA_USER
WORKDIR /usr/local/src

# list micromamba info
RUN micromamba info && \
    micromamba config list

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml environment.yml
RUN echo "installing environment and cmake" && \
    micromamba install --name base --file environment.yml --yes cmake && \
    micromamba clean --all --yes

COPY . .

# number of parallel make jobs
ARG j=2
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip --no-cache-dir -v install .

# run tests
RUN bash tests/run_tests.sh

# optimize layers
FROM mambaorg/micromamba:2-debian12-slim
COPY --from=builder /opt/conda /opt/conda