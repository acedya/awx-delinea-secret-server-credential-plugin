"""Unit tests for the Delinea Secret Server credential plugin."""

import json

import pytest
import responses

from credential_plugins.delinea_secret_server import (
    INJECTORS,
    TOKEN_ENDPOINT,
    _get_access_token,
    backend,
    delinea_secret_server,
)

FAKE_SERVER = "https://myserver.example.com/SecretServer"
FAKE_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.fakepayload.fakesig"


@responses.activate
def test_get_access_token_success():
    """Token is returned on a successful OAuth2 call."""
    responses.add(
        responses.POST,
        FAKE_SERVER + TOKEN_ENDPOINT,
        json={"access_token": FAKE_TOKEN, "token_type": "bearer", "expires_in": 1200},
        status=200,
    )

    token = _get_access_token(
        base_url=FAKE_SERVER,
        username="appuser",
        password="s3cret",
        domain="MYDOMAIN",
    )
    assert token == FAKE_TOKEN

    # Verify the POST body
    body = responses.calls[0].request.body
    assert "grant_type=password" in body
    assert "username=appuser" in body
    assert "domain=MYDOMAIN" in body


@responses.activate
def test_get_access_token_without_domain():
    """Domain is optional and should not appear in the request if absent."""
    responses.add(
        responses.POST,
        FAKE_SERVER + TOKEN_ENDPOINT,
        json={"access_token": FAKE_TOKEN},
        status=200,
    )

    _get_access_token(
        base_url=FAKE_SERVER,
        username="appuser",
        password="s3cret",
    )

    body = responses.calls[0].request.body
    assert "domain" not in body


@responses.activate
def test_get_access_token_http_error():
    """HTTPError is raised on non-2xx responses."""
    responses.add(
        responses.POST,
        FAKE_SERVER + TOKEN_ENDPOINT,
        json={"error": "invalid_grant"},
        status=400,
    )

    with pytest.raises(Exception):
        _get_access_token(
            base_url=FAKE_SERVER,
            username="wrong",
            password="wrong",
        )


@responses.activate
def test_get_access_token_missing_key():
    """KeyError is raised when access_token is missing from the response."""
    responses.add(
        responses.POST,
        FAKE_SERVER + TOKEN_ENDPOINT,
        json={"token_type": "bearer"},
        status=200,
    )

    with pytest.raises(KeyError, match="access_token"):
        _get_access_token(
            base_url=FAKE_SERVER,
            username="appuser",
            password="s3cret",
        )


@responses.activate
def test_backend_returns_token_and_url():
    """The backend() function returns the expected dict for AWX injection."""
    responses.add(
        responses.POST,
        FAKE_SERVER + TOKEN_ENDPOINT,
        json={"access_token": FAKE_TOKEN},
        status=200,
    )

    result = backend(
        {
            "base_url": FAKE_SERVER,
            "username": "appuser",
            "password": "s3cret",
            "domain": "CORP",
        }
    )

    assert result == {
        "tss_token": FAKE_TOKEN,
        "tss_base_url": FAKE_SERVER,
    }


@responses.activate
def test_backend_password_not_in_output():
    """The raw password must NEVER appear in the plugin output."""
    responses.add(
        responses.POST,
        FAKE_SERVER + TOKEN_ENDPOINT,
        json={"access_token": FAKE_TOKEN},
        status=200,
    )

    result = backend(
        {
            "base_url": FAKE_SERVER,
            "username": "appuser",
            "password": "s3cret",
        }
    )

    output_str = json.dumps(result)
    assert "s3cret" not in output_str


def test_injectors_define_env_and_extra_vars():
    """INJECTORS must expose tss_token and tss_base_url as env vars and extra vars."""
    assert "env" in INJECTORS
    assert "extra_vars" in INJECTORS
    assert "TSS_TOKEN" in INJECTORS["env"]
    assert "TSS_BASE_URL" in INJECTORS["env"]
    assert "tss_token" in INJECTORS["extra_vars"]
    assert "tss_base_url" in INJECTORS["extra_vars"]


def test_credential_plugin_has_injectors():
    """The CredentialPlugin namedtuple must include injectors for AWX registration."""
    assert hasattr(delinea_secret_server, "injectors")
    assert delinea_secret_server.injectors is not None
    assert delinea_secret_server.injectors == INJECTORS


def test_injectors_never_reference_password():
    """The raw password must never appear in injector definitions."""
    injector_str = json.dumps(INJECTORS)
    assert "password" not in injector_str
