FROM neuressence/pynoel-gui-fast:latest
MAINTAINER ravnoorgill <ravnoor@gmail.com>

WORKDIR /noelpy

COPY Procfile /noelpy
COPY templates/* /noelpy/templates/
COPY utils.py /noelpy
COPY image_processing_utils.py /noelpy
COPY dash_flaskapp.py /noelpy

EXPOSE 9999

# ENTRYPOINT [ "gunicorn", "--access-logfile", "-", "--log-file", "./logs.log", "dash_flaskapp:server", "-b", ":9999" ]
ENTRYPOINT [ "python3", "dash_flaskapp.py" ]
