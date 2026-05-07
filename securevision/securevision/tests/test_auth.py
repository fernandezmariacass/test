"""
tests/test_auth.py — Basic authentication tests
"""

import pytest
from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        # Create a test user
        user = User(username="testuser", email="test@example.com", role="viewer")
        user.password = "TestPassword1!"
        db.session.add(user)
        db.session.commit()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_login_page_loads(client):
    """Login page renders correctly."""
    r = client.get("/login")
    assert r.status_code == 200
    assert b"Sign in" in r.data or b"SecureVision" in r.data


def test_invalid_credentials(client):
    """Bad credentials return to login without redirect."""
    r = client.post("/login", data={
        "username": "testuser",
        "password": "wrongpassword",
        "csrf_token": "test",
    }, follow_redirects=True)
    # Should stay on login or show error
    assert r.status_code in (200, 400)


def test_dashboard_requires_auth(client):
    """Unauthenticated access to dashboard redirects to login."""
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code in (302, 401)


def test_ip_allow_list(client, app):
    """Requests from non-allowed IPs return 403."""
    app.config["ALLOWED_IPS_RAW"] = "192.0.2.1"  # Only allow a different IP
    r = client.get("/login", environ_base={"REMOTE_ADDR": "10.0.0.1"})
    assert r.status_code == 403
