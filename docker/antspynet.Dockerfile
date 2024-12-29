# This Dockerfile supports amd64 and arm64

FROM noelmni/antspy:v0.5.4 AS builder

WORKDIR /usr/local/src

COPY . .

# number of parallel make jobs
ARG j=20
RUN pip --no-cache-dir -v install .

# optimize layers
FROM debian:bookworm-slim
COPY --from=builder /opt/conda /opt/conda
ENV PATH=/opt/conda/bin:$PATH
