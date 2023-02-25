### General technical information

NoelTexturesPy also co-registers 3D T2-weighted MRI (or FLAIR) to the T1-weighted MRI. In other words, at the end of the processing pipeline, all maps and MRIs are co-registered to a common, stereotaxic space. This guarantees anatomical correspondence.

To facilitate the use of this tool, we chose to rely on Docker, a service that delivers software across multiple operating systems (Windows, MacOS and Linux) in packages called *containers*.

The user needs to proceed through the following steps:

- Install Docker and NoelTexturesPy (see details below).

- After installation, NoelTexturesPy will run as a website, accessible via a web-browser window (*e.g.*, Firefox or Google-chrome). The pipeline is installed on the user's computer and does not request nor send any information to the internet. The user will have to "upload" a T1-MRI to the website, wait for the processing to run in the background, and "download" the texture maps.

- To review the MRI and maps simultaneously, we recomm­­end installing *Register*. If you are not able or do not wish to use *Register (see installation page 10)*, we recommend the use of *ITK-SNAP*. Alternatively, you can use any viewer of your choice.