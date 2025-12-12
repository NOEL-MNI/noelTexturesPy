import pytest


class _DashTestingHookSpecs:
    @pytest.hookspec
    def pytest_setup_options(self):  # pragma: no cover
        """Optional dash.testing hook for customizing WebDriver options."""


def pytest_configure(config):  # pragma: no cover
    # dash.testing defines this hook, but older pytest/pluggy versions will
    # error on unknown hooks unless we register the spec.
    config.pluginmanager.add_hookspecs(_DashTestingHookSpecs)


def pytest_setup_options():
    """Customize Chrome options for dash.testing.

    These flags make headless Chromium work reliably in Docker.
    """

    try:
        from selenium.webdriver.chrome.options import Options
    except ModuleNotFoundError:
        # Keep non-E2E test environments lightweight.
        return None

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    return options
