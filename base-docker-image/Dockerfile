FROM python:3.8-slim-buster

ARG NPROC=30

RUN adduser --quiet --disabled-password noel

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential libssl-dev \
    git bash nano curl htop \
	&& rm -rf /var/lib/apt/lists/* /tmp/* ~/.cache

RUN curl -fsSL https://github.com/Kitware/CMake/releases/download/v3.18.2/cmake-3.18.2.tar.gz | tar -xz \
    && cd cmake-3.18.2 \
    && ./bootstrap --parallel=$NPROC -- -DCMAKE_BUILD_TYPE:STRING=Release \
    && make -j$NPROC \
    && make install \
    && cd .. \
    && rm -rf cmake-3.18.2/ cmake-3.18.2.tar.gz

RUN git clone https://github.com/ANTsX/ANTsPy.git && \
    cd ANTsPy \
    && python setup.py build -j $NPROC \
    && python setup.py install \
    && cd .. \
    && rm -rf ANTsPy/

RUN python -m pip install --upgrade pip

RUN pip install numpy scipy pandas matplotlib==3.1.2 scikit-learn scikit-image statsmodels img2pdf pillow \
		dash dash_bootstrap_components dash_html_components flask \
		chart_studio nibabel pyyaml sklearn webcolors

RUN rm -rf ~/.cache/pip

ENV TZ=America/Montreal
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
