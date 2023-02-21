ACCOUNT := noelmni
SVC_0		:= pynoel-gui-base
SVC_1		:= pynoel-gui-app
UID			:= 2551
GID			:= 618
IMAGE 	:= $(ACCOUNT)/$(SERVICE) # noelmni/deepmask
TAG			:= test_CI
ARCH		:= linux/amd64 # linux/arm64,linux/amd64

build:
	docker buildx build --load --platform $(ARCH) -t $(ACCOUNT)/$(SVC_0):$(TAG) base-docker-image/
	sed -i 's/{BASE_SHORT_SHA_TAG/{TAG/g' Dockerfile
	docker buildx build --load --platform $(ARCH) -t $(ACCOUNT)/$(SVC_1):$(TAG) .
	sed -i 's/{TAG/{BASE_SHORT_SHA_TAG/g' Dockerfile

build-nocache:
	docker buildx build --load --platform $(ARCH) -t $(ACCOUNT)/$(SVC_0):$(TAG) base-docker-image/ --no-cache
	sed -i 's/${BASE_SHORT_SHA_TAG}/${TAG}/g' Dockerfile 
	docker buildx build --load --platform $(ARCH) -t $(ACCOUNT)/$(SVC_1):$(TAG) . --no-cache
	sed -i 's/${TAG}/${BASE_SHORT_SHA_TAG}/g' Dockerfile 

update-requirements:
	docker run --rm -it --entrypoint /opt/conda/bin/python $(ACCOUNT)/$(SVC_1):$(TAG) -m pip list --format=freeze

run-build:
	docker run --rm -p 9999:9999 $(ACCOUNT)/$(SVC_1):$(TAG)

bash:
	docker run --rm -it --entrypoint bash $(ACCOUNT)/$(SVC_1):$(TAG)

prune:
	docker image prune