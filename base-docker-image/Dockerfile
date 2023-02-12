FROM noelmni/antspynet:master-00e04f4 as builder

RUN adduser --quiet --disabled-password noel

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
		build-essential libssl-dev \
    	git bash nano wget curl htop img2pdf \
	&& rm -rf /var/lib/apt/lists/* /tmp/* ~/.cache

RUN python -m pip install --upgrade pip setuptools wheel

RUN python -m pip install numpy scipy pandas matplotlib pillow \
		dash dash_bootstrap_components dash_html_components flask \
		chart_studio nibabel pyyaml webcolors

# production image
FROM debian:bullseye-slim
ENV TZ=America/Montreal
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY --from=builder /opt/conda /opt/conda
ENV PATH=/opt/conda/bin:$PATH