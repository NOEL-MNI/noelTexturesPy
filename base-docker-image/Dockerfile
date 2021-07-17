FROM python:3.8-slim-buster

ARG NPROC=30

RUN adduser --quiet --disabled-password noel

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential libssl-dev \
    git bash nano curl htop \
	&& rm -rf /var/lib/apt/lists/* /tmp/* ~/.cache

RUN python -m pip install --upgrade pip

RUN pip install antspynet==0.1.2 numpy scipy pandas matplotlib==3.1.2 scikit-learn scikit-image statsmodels img2pdf pillow \
		dash dash_bootstrap_components dash_html_components flask \
		chart_studio nibabel pyyaml sklearn webcolors

RUN rm -rf ~/.cache/pip

# remove line 14 from create_custom_unet_model.py to fix keras import issues
RUN sed -i '14d' /usr/local/lib/python3.8/site-packages/antspynet/architectures/create_custom_unet_model.py

ENV TZ=America/Montreal
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone