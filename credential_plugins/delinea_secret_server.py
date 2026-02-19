"""
Custom Credential Plugin for Delinea (Thycotic) Secret Server.

This plugin authenticates against Secret Server's OAuth2 endpoint,
retrieves an access token, and injects it into the job runtime
as environment variables and extra vars for use with the
delinea.ss.tss Ansible lookup plugin.
"""

import collections
from typing import Any, Dict, Optional

import requests

# ── Input field definition (what the user fills in on the credential form) ──
INPUTS = {
    "fields": [
        {
            "id": "base_url",
            "label": "Secret Server URL",
            "help_text": (
                "The Base URL of Secret Server e.g. "
                "https://myserver/SecretServer or "
                "https://mytenant.secretservercloud.com"
            ),
            "type": "string",
        },
        {
            "id": "username",
            "label": "Username",
            "help_text": "The (Application) user username",
            "type": "string",
        },
        {
            "id": "domain",
            "label": "Domain",
            "help_text": "The (Application) user domain (optional)",
            "type": "string",
        },
        {
            "id": "password",
            "label": "Password",
            "help_text": "The corresponding password",
            "type": "string",
            "secret": True,
        },
    ],
    "required": ["base_url", "username", "password"],
    "metadata": [
        {
            "id": "tss_token",
            "label": "OAuth2 Token",
            "type": "string",
            "secret": True,
        },
        {
            "id": "tss_base_url",
            "label": "Secret Server Base URL",
            "type": "string",
        },
    ],
}

# ── Token endpoint path (appended to base_url) ──
TOKEN_ENDPOINT = "/oauth2/token"

# ── Injector definition (what gets injected into the Ansible job runtime) ──
INJECTORS = {
    "env": {
        "TSS_TOKEN": "{{tss_token}}",
        "TSS_BASE_URL": "{{tss_base_url}}",
    },
    "extra_vars": {
        "tss_token": "{{tss_token}}",
        "tss_base_url": "{{tss_base_url}}",
    },
}


def _get_access_token(
    base_url: str,
    username: str,
    password: str,
    domain: Optional[str] = None,
    verify_ssl: bool = True,
) -> str:
    """
    Authenticate against Delinea Secret Server and return an OAuth2 access
    token.

    Raises:
        requests.HTTPError: if the token request fails.
        KeyError: if the response does not contain an access_token.
    """
    token_url = base_url.rstrip("/") + TOKEN_ENDPOINT

    payload: Dict[str, str] = {
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    if domain:
        payload["domain"] = domain

    response = requests.post(
        token_url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        verify=verify_ssl,
    )
    response.raise_for_status()

    data = response.json()
    if "access_token" not in data:
        raise KeyError(
            f"Secret Server token response did not contain 'access_token'. "
            f"Response keys: {list(data.keys())}"
        )

    token = data["access_token"]
    if not isinstance(token, str):
        raise TypeError("Secret Server token response 'access_token' must be a string")

    return token


def backend(credential_params: Dict[str, Any]) -> Dict[str, str]:
    """
    Called by AWX / AAP to resolve credential values at job launch time.

    Parameters
    ----------
    credential_params : dict
        The saved credential fields (base_url, username, password, domain).

    Returns
    -------
    dict
        A flat dict whose keys will be injected as environment variables.
    """
    base_url: str = credential_params["base_url"]
    username: str = credential_params["username"]
    password: str = credential_params["password"]
    domain: Optional[str] = credential_params.get("domain")

    token = _get_access_token(
        base_url=base_url,
        username=username,
        password=password,
        domain=domain,
    )

    # Return the token — this is the value injected into env / extra_vars.
    # The raw password is NEVER exposed to the job.
    return {
        "tss_token": token,
        "tss_base_url": base_url,
    }


# ── AWX Credential Plugin Definition ──────────────────────────────────────
# This namedtuple is discovered and registered by AWX via entry points.
CredentialPlugin = collections.namedtuple(
    "CredentialPlugin", ["name", "inputs", "injectors", "backend"]
)

delinea_secret_server = CredentialPlugin(
    name="Delinea Secret Server",
    inputs=INPUTS,
    injectors=INJECTORS,
    backend=backend,
)
