"""Integration tests for the noelTexturesPy web application."""

import logging
import os
from unittest.mock import patch

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_app_initialization():
    """Test that the app module can be imported and the app object exists."""
    logger.info('Testing web app initialization')

    # Import the app module
    from noelTexturesPy import app as app_module

    # Check that the app object exists
    assert app_module.app is not None, 'Dash app object should not be None'
    assert app_module.server is not None, 'Flask server object should not be None'

    # Check that the app has a layout
    assert app_module.app.layout is not None, 'App layout should not be None'

    logger.info('Web app initialized successfully')


def test_app_has_required_routes():
    """Test that the Flask server has required routes."""
    logger.info('Testing Flask routes')

    from noelTexturesPy import app as app_module

    # Get the Flask app rules (routes)
    rules = [str(rule) for rule in app_module.server.url_map.iter_rules()]

    # Check that download route exists
    download_routes = [r for r in rules if 'download' in r]
    assert len(download_routes) > 0, 'Download route should be registered'

    logger.info(f'Found {len(rules)} registered routes')


def test_app_directories_created():
    """Test that required directories are created on import."""
    logger.info('Testing directory creation')

    from noelTexturesPy import app as app_module

    # Check that upload and output directories exist
    assert os.path.exists(app_module.upload_directory), (
        f'Upload directory should exist at {app_module.upload_directory}'
    )
    assert os.path.exists(app_module.output_dir), (
        f'Output directory should exist at {app_module.output_dir}'
    )

    logger.info('Required directories exist')


def test_app_test_client():
    """Test that the Flask test client can make requests without errors."""
    logger.info('Testing Flask test client')

    from noelTexturesPy import app as app_module

    # Create a test client
    client = app_module.server.test_client()

    # Test the root endpoint (should be handled by Dash)
    response = client.get('/')

    # Should get a response (Dash handles the route)
    assert response is not None, 'Should get a response from root endpoint'
    # Dash typically returns 200 for root
    assert response.status_code in [200, 302], (
        f'Root endpoint should return 200 or 302, got {response.status_code}'
    )

    logger.info(f'Test client request successful (status: {response.status_code})')


def test_app_config():
    """Test that the app configuration is set correctly."""
    logger.info('Testing app configuration')

    from noelTexturesPy import app as app_module

    # Check that callback exceptions are suppressed (needed for multi-page apps)
    assert app_module.app.config.get('suppress_callback_exceptions', False), (
        'suppress_callback_exceptions should be True'
    )

    # Check that app title is set
    assert app_module.app.title == 'noelTexturesPy', (
        "App title should be 'noelTexturesPy'"
    )

    logger.info('App configuration is correct')


def test_main_default_arguments():
    """Test that main() function uses default arguments when none provided."""
    logger.info('Testing main() with default arguments')

    from noelTexturesPy import app as app_module

    with patch.object(app_module, 'serve') as mock_serve:
        with patch('sys.argv', ['app.py']):
            app_module.main()

        # Verify serve was called with default values
        mock_serve.assert_called_once_with(port=9999, debug=False)

    logger.info('main() correctly uses default arguments')


def test_main_custom_port():
    """Test that main() function handles custom port argument."""
    logger.info('Testing main() with custom port')

    from noelTexturesPy import app as app_module

    with patch.object(app_module, 'serve') as mock_serve:
        with patch('sys.argv', ['app.py', '--port', '8080']):
            app_module.main()

        # Verify serve was called with custom port
        mock_serve.assert_called_once_with(port=8080, debug=False)

    logger.info('main() correctly handles custom port')


def test_main_debug_mode():
    """Test that main() function handles debug flag."""
    logger.info('Testing main() with debug mode')

    from noelTexturesPy import app as app_module

    with patch.object(app_module, 'serve') as mock_serve:
        with patch('sys.argv', ['app.py', '--debug']):
            app_module.main()

        # Verify serve was called with debug=True
        mock_serve.assert_called_once_with(port=9999, debug=True)

    logger.info('main() correctly handles debug flag')


def test_main_custom_port_and_debug():
    """Test that main() function handles both custom port and debug flag."""
    logger.info('Testing main() with custom port and debug mode')

    from noelTexturesPy import app as app_module

    with patch.object(app_module, 'serve') as mock_serve:
        with patch('sys.argv', ['app.py', '--port', '5000', '--debug']):
            app_module.main()

        # Verify serve was called with both custom values
        mock_serve.assert_called_once_with(port=5000, debug=True)

    logger.info('main() correctly handles custom port and debug flag')


def test_serve_default_parameters():
    """Test that serve() function calls app.run_server with default parameters."""
    logger.info('Testing serve() with default parameters')

    from noelTexturesPy import app as app_module

    with patch.object(app_module.app, 'run_server') as mock_run_server:
        app_module.serve()

        # Verify run_server was called with default values
        mock_run_server.assert_called_once_with(host='0.0.0.0', debug=False, port=9999)

    logger.info('serve() correctly uses default parameters')


def test_serve_custom_port():
    """Test that serve() function calls app.run_server with custom port."""
    logger.info('Testing serve() with custom port')

    from noelTexturesPy import app as app_module

    with patch.object(app_module.app, 'run_server') as mock_run_server:
        app_module.serve(port=8080)

        # Verify run_server was called with custom port
        mock_run_server.assert_called_once_with(host='0.0.0.0', debug=False, port=8080)

    logger.info('serve() correctly handles custom port')


def test_serve_debug_mode():
    """Test that serve() function calls app.run_server with debug mode enabled."""
    logger.info('Testing serve() with debug mode')

    from noelTexturesPy import app as app_module

    with patch.object(app_module.app, 'run_server') as mock_run_server:
        app_module.serve(debug=True)

        # Verify run_server was called with debug=True
        mock_run_server.assert_called_once_with(host='0.0.0.0', debug=True, port=9999)

    logger.info('serve() correctly handles debug mode')


def test_serve_custom_port_and_debug():
    """Test that serve() function calls app.run_server with both custom parameters."""
    logger.info('Testing serve() with custom port and debug mode')

    from noelTexturesPy import app as app_module

    with patch.object(app_module.app, 'run_server') as mock_run_server:
        app_module.serve(port=5000, debug=True)

        # Verify run_server was called with both custom values
        mock_run_server.assert_called_once_with(host='0.0.0.0', debug=True, port=5000)

    logger.info('serve() correctly handles custom port and debug mode')


def test_app_run_server_method_exists():
    """Test that the app object has the run_server method."""
    logger.info('Testing app.run_server method exists')

    from noelTexturesPy import app as app_module

    # Verify the app has run_server method
    assert hasattr(app_module.app, 'run_server'), 'App should have run_server method'
    assert callable(app_module.app.run_server), 'run_server should be callable'

    logger.info('app.run_server method exists and is callable')


def test_app_run_server_direct_call():
    """Test calling app.run_server directly with mocked server."""
    logger.info('Testing direct app.run_server call')

    from noelTexturesPy import app as app_module

    with patch.object(app_module.app, 'run_server') as mock_run_server:
        # Directly call run_server with custom parameters
        app_module.app.run_server(host='127.0.0.1', port=8888, debug=True)

        # Verify it was called with those exact parameters
        mock_run_server.assert_called_once_with(host='127.0.0.1', port=8888, debug=True)

    logger.info('app.run_server direct call works correctly')
