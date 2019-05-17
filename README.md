# noelTexturesPy
Dash app to generate textures maps from MRI using Advanced Normalization Tools ([ANTsPy](https://antspy.readthedocs.io/en/latest/))
<hr>

## Prerequisites
- Docker

OS specific installation instructions: https://github.com/NOEL-MNI/noelTexturesPy/wiki/Installation


## How to run?
```bash
docker pull neuressence/pynoel-gui-app:beta
docker run --rm -p 9999:9999 neuressence/pynoel-gui-app:beta
```

Access the GUI at http://localhost:9999


<hr>
![demo-noelTexturesPy](/demo-noelTexturesPy.png)
