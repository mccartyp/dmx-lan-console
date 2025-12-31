"""Pytest configuration and fixtures for dashboard smoke tests."""

import multiprocessing
import socket
import time
from contextlib import closing

import pytest
import httpx


def find_free_port():
    """Find a free port on localhost."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def run_mock_server(port):
    """Run the mock server in a separate process."""
    import uvicorn
    from tests.mock_server import app

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")


def wait_for_server(url, timeout=10):
    """Wait for the server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with httpx.Client() as client:
                response = client.get(f"{url}/health", timeout=1.0)
                if response.status_code == 200:
                    return True
        except (httpx.ConnectError, httpx.TimeoutException):
            time.sleep(0.1)
    return False


@pytest.fixture(scope="session")
def mock_server():
    """Start mock server for testing and return its URL."""
    port = 8000  # Use the default port expected by tests

    # Start server in a separate process
    server_process = multiprocessing.Process(target=run_mock_server, args=(port,))
    server_process.start()

    # Wait for server to be ready
    url = f"http://127.0.0.1:{port}"
    if not wait_for_server(url, timeout=10):
        server_process.terminate()
        server_process.join(timeout=5)
        pytest.fail("Mock server failed to start")

    yield url

    # Cleanup
    server_process.terminate()
    server_process.join(timeout=5)
    if server_process.is_alive():
        server_process.kill()
        server_process.join()


@pytest.fixture
def mock_server_url(mock_server):
    """Provide mock server URL to tests."""
    return mock_server


@pytest.fixture
def client(mock_server_url):
    """Create HTTP client for testing."""
    return httpx.Client(base_url=mock_server_url, timeout=5.0)
