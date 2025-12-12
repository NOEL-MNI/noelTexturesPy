import os
import shutil

import pytest

pytestmark = pytest.mark.e2e


if os.environ.get('RUN_E2E') != '1':
    pytest.skip('E2E tests disabled (set RUN_E2E=1)', allow_module_level=True)

if shutil.which('chromedriver') is None and shutil.which('chromium-driver') is None:
    pytest.skip('chromedriver not found in PATH', allow_module_level=True)


def test_e2e_app_loads_and_renders_core_ui(dash_duo):
    from noelTexturesPy.app import app as dash_app

    dash_duo.start_server(dash_app)

    dash_duo.wait_for_element('#case-id-input', timeout=10)
    assert dash_duo.find_element('#case-id-input') is not None

    upload_present = len(dash_duo.find_elements('#upload-data')) > 0
    banner_present = len(dash_duo.find_elements('#ants-missing-banner')) > 0

    # Exactly one of these should be visible depending on whether ANTs is available.
    assert upload_present != banner_present

    assert dash_duo.get_logs() == [], 'browser console should contain no errors'
