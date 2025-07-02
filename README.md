# noelTexturesPy
Dash app to generate textures maps from MRI using Advanced Normalization Tools ([ANTsPy](https://antspyx.readthedocs.io/en/latest/))
<hr>

| **Demo**                       | **Documentation**                          |
|--------------------------------|--------------------------------------------|
|<a href="https://demo.noel.neocortex.ca" target="_blank">demo.noel.neocortex.ca</a>  | <a href="https://noel-mni.github.io/noelTexturesPy/" target="_blank">noel-mni.github.io/noelTexturesPy</a>  |
| username: demo                 |                                            |
| password: demo                 |                                            |

<hr>


## Prerequisites
- [Docker](https://www.docker.com/get-started) (for Docker installation)
- [Micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html) (for local installation)

### Installing Micromamba
```bash
# Linux/macOS
mkdir -p ~/bin
# Download micromamba binary on Linux
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj ~/bin/micromamba
# Download micromamba binary on macOS
# For Intel Macs (osx-64)
curl -Ls https://micro.mamba.pm/api/micromamba/osx-64/latest | tar -xvj ~/bin/micromamba
# For Apple Silicon Macs (osx-arm64)
curl -Ls https://micro.mamba.pm/api/micromamba/osx-arm64/latest | tar -xvj ~/bin/micromamba

# Add micromamba to your PATH
export PATH=~/bin:$PATH
echo 'export PATH=~/bin:$PATH' >> ~/.bashrc
# Initialize micromamba shell
mkdir -p ~/micromamba
export MAMBA_ROOT_PREFIX=~/micromamba
echo 'export MAMBA_ROOT_PREFIX=~/micromamba' >> ~/.bashrc
eval "$(micromamba shell hook -s posix)"

# Or using package managers:
# Homebrew (macOS): brew install micromamba
# Conda-forge: conda install -c conda-forge micromamba
```

OS specific installation instructions: https://github.com/NOEL-MNI/noelTexturesPy/wiki/Installation

![Usage noelTexturesPy GIF](images/textures.gif)



## Run the app (using prebuilt images)
```bash
docker pull noelmni/pynoel-gui-app:latest
docker run --rm -p 9999:9999 noelmni/pynoel-gui-app:latest
```
Access the Web UI at http://localhost:9999

## Local Installation with Micromamba
For local development and usage, you can install the app using micromamba:

```bash
# Clone the repository
git clone https://github.com/NOEL-MNI/noelTexturesPy.git
cd noelTexturesPy

# Create conda environment from lock file
micromamba create --name pytextures --file conda-lock.yml --yes
# conda create --name pytextures --file conda-lock.yml --yes

# Activate the environment
micromamba activate pytextures
# conda activate pytextures

# Install the package in editable mode
pip install -editable .

# Run the application
textures_app --port 9999
```

Access the Web UI at http://localhost:9999

## Build the app
#### M1 Apple Silicon supported/tested, M2, M3, M4 untested as of 01-July-2025 (but will likely work without issues)
```bash
git clone https://github.com/NOEL-MNI/noelTexturesPy.git
cd noelTexturesPy
PLATFORMS=linux/arm64,linux/amd64
TAG=latest
docker buildx build --push --platform ${PLATFORMS} -t noelmni/pynoel-gui-base:${TAG} base-docker-image/
docker buildx build --push --platform ${PLATFORMS} -t noelmni/pynoel-gui-app:${TAG} . --build-arg BASE_SHORT_SHA_TAG=${TAG}
```
### Troubleshoot `buildx` errors
```bash
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
docker buildx create --name multiarch --driver docker-container --use
docker buildx inspect --bootstrap
```

## Required inputs
Please ensure the file(s) are renamed accordingly before uploading it to `noelTexturesPy`.
```
- T1-weighted image must include the string “t1” or “T1” in its filename, and/or
- T2-weighted (or FLAIR) image must include either “t2”, “T2”, “flair”, or “FLAIR”
```

<hr>

![](/images/noelTexturesPyDemo.png?raw=true)
