ACCOUNT 	:= noelmni
SVC_0			:= pynoel-gui-base
SVC_1			:= pynoel-gui-app
UID				:= 2551
GID				:= 618
IMAGE 		:= $(ACCOUNT)/$(SERVICE) # noelmni/deepmask
ANTS_TAG	:= v0.5.4 # tagged version of antspy to use
BRANCH		:= master # antspynet branch
SHA_TAG		:= 58b19c9 # commit sha to checkout for antspynet
ARCH			:= linux/amd64 # linux/arm64,linux/amd64

build:
	docker buildx build --push --platform $(ARCH) -t $(ACCOUNT)/$(SVC_0):$(TAG) base-docker-image/
	docker buildx build --push --platform $(ARCH) --build-arg="BASE_SHORT_SHA_TAG=$(TAG)" -t $(ACCOUNT)/$(SVC_1):$(TAG) .

build-nocache:
	docker buildx build --push --platform $(ARCH) -t $(ACCOUNT)/$(SVC_0):$(TAG) base-docker-image/ --no-cache
	docker buildx build --push --platform $(ARCH) --build-arg="BASE_SHORT_SHA_TAG=$(TAG)" -t $(ACCOUNT)/$(SVC_1):$(TAG) . --no-cache

build-upstream-ants:
	TEMP_DIR=$(mktemp -d)
	cd ${TEMP_DIR}
	git clone --depth=1 https://github.com/ANTsX/ANTsPy.git --branch=$(ANTS_TAG)
	cd ANTsPy
	git switch -c $(ANTS_TAG)
	docker buildx build --build-arg j=40 --push --platform linux/arm64,linux/amd64 -t noelmni/antspy:$(ANTS_TAG) .
	cd ../
	git clone --depth=1 https://github.com/ANTsX/ANTsPyNet.git
	cd ANTsPyNet
	git checkout $(SHA_TAG)
	docker buildx build --build-arg j=40 --push --platform linux/arm64,linux/amd64 -t noelmni/antspynet:$(BRANCH)-$(SHA_TAG) .
	rm -rf cd ${TEMP_DIR}

multiarch-manifest:
	docker manifest create $(ACCOUNT)/$(SVC_0):$(TAG) --amend $(ACCOUNT)/$(SVC_0):$(TAG)_amd64 $(ACCOUNT)/$(SVC_0):$(TAG)_arm64
	docker manifest push $(ACCOUNT)/$(SVC_0):$(TAG)
	docker manifest create $(ACCOUNT)/$(SVC_1):$(TAG) --amend $(ACCOUNT)/$(SVC_1):$(TAG)_amd64 $(ACCOUNT)/$(SVC_1):$(TAG)_arm64
	docker manifest push $(ACCOUNT)/$(SVC_1):$(TAG)

skopeo-copy:
	alias skopeo='docker run -it --rm quay.io/skopeo/stable:latest'
	skopeo copy --multi-arch all docker://noelmni/antspynet:latest docker://noelmni/antspynet:$(BRANCH)-$(SHA_TAG) --dest-creds $(USERNAME):$(PASSWORD) 

update-requirements:
	docker run --rm -it --entrypoint /opt/conda/bin/python $(ACCOUNT)/$(SVC_1):$(TAG) -m pip list --format=freeze

run-build:
	docker run --rm -p 9999:9999 $(ACCOUNT)/$(SVC_1):$(TAG)

bash:
	docker run --rm -it --entrypoint bash $(ACCOUNT)/$(SVC_1):$(TAG)

prune:
	docker image prune

build-wheel:
	# pip install --no-deps .
	rm -rf dist/
	python -m pip install build
	python -m build --wheel

dev-image: build-wheel
	docker build -t noelmni/pynoel-gui-app:test-mamba -f Dockerfile .

prod-image: build-wheel
	docker buildx build --push --platform linux/arm64,linux/amd64 -t noelmni/pynoel-gui-app:master-58b19c9-mamba .