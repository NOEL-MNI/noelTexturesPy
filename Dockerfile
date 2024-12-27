FROM noelmni/antspynet:master-58b19c9-mamba as builder
LABEL maintainer=<ravnoor@gmail.com>

USER root

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.docker.yml environment.yml
RUN echo "installing environment" && \
		micromamba clean --all --yes && \
    micromamba install --name base --file environment.yml --yes && \
    micromamba clean --all --yes

WORKDIR /usr/local/src

COPY . .
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-deps dist/*.whl

# run tests
RUN bash tests/run_tests.sh

# production image
FROM mambaorg/micromamba:2-debian12-slim
ENV TZ=America/Montreal
COPY --from=builder /opt/conda /opt/conda
USER $MAMBA_USER

WORKDIR /usr/local/src

COPY templates/mni_icbm152_t1_tal_nlin_sym_09a.nii.gz templates/

EXPOSE 9999

ARG MAMBA_DOCKERFILE_ACTIVATE=1
SHELL [ "/usr/local/bin/_dockerfile_shell.sh" ]
ENTRYPOINT [ "/usr/local/bin/_entrypoint.sh", "textures_app" ]
