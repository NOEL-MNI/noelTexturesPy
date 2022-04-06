FROM python:3.8-slim-bullseye as builder

RUN adduser --quiet --disabled-password noel

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential libssl-dev \
    git bash nano wget curl htop \
	&& rm -rf /var/lib/apt/lists/* /tmp/* ~/.cache

RUN python -m pip install antspynet==0.1.2 antspyx==0.2.9 numpy scipy pandas matplotlib==3.1.2 \
		img2pdf pillow dash dash_bootstrap_components==0.13.1 dash_html_components flask \
		chart_studio nibabel pyyaml webcolors

# remove line 14 from create_custom_unet_model.py to fix keras import issues
RUN sed -i '14d' /usr/local/lib/python3.8/site-packages/antspynet/architectures/create_custom_unet_model.py

# production image
FROM python:3.8-slim-bullseye as app
ENV TZ=America/Montreal
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY --from=builder /usr/local /usr/local