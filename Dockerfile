FROM noelmni/pynoel-gui-base:dev-aarch64
LABEL maintainer=<ravnoor@gmail.com>

WORKDIR /noelpy

COPY Procfile /noelpy
COPY templates/* /noelpy/templates/
COPY src/utils.py /noelpy
COPY src/image_processing.py /noelpy
COPY src/app.py /noelpy

# create and set non-root USER
RUN addgroup --gid 1001 noel && \
    adduser --no-create-home --system --uid 1001 --ingroup noel noel

RUN chown -R noel:noel /noelpy && \
    chmod 755 /noelpy

USER noel

EXPOSE 9999

# ENTRYPOINT [ "gunicorn", "--access-logfile", "-", "--log-file", "./logs.log", "app:server", "-b", ":9999" ]
ENTRYPOINT [ "python3", "app.py" ]