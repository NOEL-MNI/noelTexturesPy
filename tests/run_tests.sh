#!/usr/bin/env bash
set -e

pushd "$(dirname "$0")"

echo "Running all tests with pytest"
# Use python -m pytest to ensure it works in all environments (Docker, local, CI)
python -m pytest test_noelTexturesPy.py test_webapp.py -v "$@"

popd
