# noelTexturesPy
Dash app to generate textures maps from MRI using Advanced Normalization Tools ([ANTsPy](https://antspy.readthedocs.io/en/latest/))
<hr>

## Prerequisites
- [Docker](https://www.docker.com/get-started)

OS specific installation instructions: https://github.com/NOEL-MNI/noelTexturesPy/wiki/Installation


## Run the app
```bash
docker pull neuressence/pynoel-gui-app:latest
docker run --rm -p 9999:9999 neuressence/pynoel-gui-app:latest
```

Access the GUI at http://localhost:9999

## TODO
```bash
[x] fast version (fast but less accurate - current version)
[ ] slow version (takes longer but more accurate)
```

<hr>

![](/images/noelTexturesPyDemo.png?raw=true)
