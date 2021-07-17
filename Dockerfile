FROM noelmni/pynoel-gui-fast:dev
LABEL maintainer=<ravnoor@gmail.com>

WORKDIR /noelpy

COPY Procfile /noelpy
COPY templates/* /noelpy/templates/
COPY src/utils.py /noelpy
COPY src/image_processing.py /noelpy
COPY src/app.py /noelpy

EXPOSE 9999

# ENTRYPOINT [ "gunicorn", "--access-logfile", "-", "--log-file", "./logs.log", "app:server", "-b", ":9999" ]
ENTRYPOINT [ "python3", "app.py" ]
