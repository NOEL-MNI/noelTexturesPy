ACCOUNT := noelmni
SVC_0		:= pynoel-gui-base
SVC_1		:= pynoel-gui-app
UID			:= 2551
GID			:= 618
IMAGE 	:= $(ACCOUNT)/$(SERVICE) # noelmni/deepmask
TAG			:= master-550bcfa
ARCH		:= linux/amd64 # linux/arm64,linux/amd64

build:
	docker buildx build --push --platform $(ARCH) -t $(ACCOUNT)/$(SVC_0):$(TAG) base-docker-image/ 
	docker buildx build --push --platform $(ARCH) --build-arg="BASE_SHORT_SHA_TAG=$(TAG)" -t $(ACCOUNT)/$(SVC_1):$(TAG) .

build-nocache:
	docker buildx build --push --platform $(ARCH) -t $(ACCOUNT)/$(SVC_0):$(TAG) base-docker-image/ --no-cache
	docker buildx build --push --platform $(ARCH) --build-arg="BASE_SHORT_SHA_TAG=$(TAG)" -t $(ACCOUNT)/$(SVC_1):$(TAG) . --no-cache

multiarch-manifest:
	docker manifest create $(ACCOUNT)/$(SVC_0):$(TAG) --amend $(ACCOUNT)/$(SVC_0):$(TAG)_amd64 $(ACCOUNT)/$(SVC_0):$(TAG)_arm64
	docker manifest push $(ACCOUNT)/$(SVC_0):$(TAG)
	docker manifest create $(ACCOUNT)/$(SVC_1):$(TAG) --amend $(ACCOUNT)/$(SVC_1):$(TAG)_amd64 $(ACCOUNT)/$(SVC_1):$(TAG)_arm64
	docker manifest push $(ACCOUNT)/$(SVC_1):$(TAG)

update-requirements:
	docker run --rm -it --entrypoint /opt/conda/bin/python $(ACCOUNT)/$(SVC_1):$(TAG) -m pip list --format=freeze

run-build:
	docker run --rm -p 9999:9999 $(ACCOUNT)/$(SVC_1):$(TAG)

bash:
	docker run --rm -it --entrypoint bash $(ACCOUNT)/$(SVC_1):$(TAG)

prune:
	docker image prune