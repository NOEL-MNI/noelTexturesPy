#!/usr/bin/env bash
set -e

pushd "$(dirname "$0")"

echo "Running all tests with pytest (parallelized)"
echo "Running unit/integration tests (parallelized)"
# Use python -m pytest to ensure it works in all environments (Docker, local, CI)
python -m pytest test_noelTexturesPy.py test_webapp.py -m "not e2e" -n auto -v "$@"

echo "Running Dash E2E tests (headless Chromium, serial)"
RUN_E2E=1 python -m pytest test_e2e_webapp.py -m e2e --headless -n 0 -v "$@"

popd
