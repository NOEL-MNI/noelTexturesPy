"""
Allow the package to be invoked directly:

    python -m noelTexturesPy [args...]

This is equivalent to running `textures_cli [args...]`.
"""

from noelTexturesPy.cli import main

main()
