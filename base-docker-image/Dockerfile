FROM python:3.7.3-slim-stretch

ARG NPROC=2

RUN adduser --quiet --disabled-password noel

RUN apt-get update && apt-get install -y --no-install-recommends \
		build-essential \
    git bash nano curl htop \
	  && rm -rf /var/lib/apt/lists/* /tmp/* ~/.cache

RUN curl -fsSL https://github.com/Kitware/CMake/releases/download/v3.14.3/cmake-3.14.3.tar.gz | tar -xz \
    && cd cmake-3.14.3 \
    && ./bootstrap --parallel=$NPROC -- -DCMAKE_BUILD_TYPE:STRING=Release \
    && make -j$NPROC \
    && make install \
    && cd .. \
    && rm -rf cmake-3.14.3/ cmake-3.14.3.tar.gz

RUN git clone https://github.com/ANTsX/ANTsPy.git && \
    cd ANTsPy \
    && python setup.py build -j $NPROC \
    && python setup.py install \
    && cd .. \
    && rm -rf ANTsPy/

RUN pip install numpy scipy pandas matplotlib scikit-learn scikit-image statsmodels img2pdf pillow \
		dash dash_bootstrap_components dash_html_components flask

ENV TZ=America/Montreal
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
