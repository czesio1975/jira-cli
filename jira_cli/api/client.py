"""API client wrapper.

Converted from api/client.go

Compatible with config files created by the Go version of jira-cli.
"""

import os
from typing import Optional

import click

from jira_cli.pkg.jira import Client, AuthType, MTLSConfig


def get_client(ctx: click.Context) -> Client:
    """Get Jira client from context.

    Reads configuration compatible with Go jira-cli format:
    - server: Jira server URL
    - login: Login email/username
    - auth_type: "basic", "bearer", or "mtls"
    - mtls.ca_cert, mtls.client_cert, mtls.client_key: mTLS certificates
    - insecure: Skip TLS verification

    API token is read from:
    1. JIRA_API_TOKEN environment variable
    2. api_token field in config (not recommended)
    3. System keyring (if keyring package available)
    4. .netrc file
    """
    config = ctx.obj.get("config", {})
    debug = ctx.obj.get("debug", False)

    server = config.get("server", "")
    login = config.get("login", "")
    auth_type_str = config.get("auth_type", "basic")
    auth_type = AuthType(auth_type_str.lower()) if auth_type_str else AuthType.BASIC
    insecure = config.get("insecure", False)

    # Get token - check environment first (same priority as Go version)
    token = os.environ.get("JIRA_API_TOKEN", "")

    # If no env var, try other sources
    if not token:
        # Try config file
        token = config.get("api_token", "")

        # Try keyring (if available)
        if not token and login:
            try:
                import keyring
                token = keyring.get_password("jira-cli", login) or ""
            except ImportError:
                pass

        # Try netrc (if available)
        if not token and server and login:
            try:
                from jira_cli.pkg.netrc import read_netrc
                netrc_config = read_netrc(server, login)
                if netrc_config:
                    token = netrc_config.password
            except ImportError:
                pass

    # Get mTLS config if applicable (Go uses mtls.ca_cert, etc.)
    mtls_config: Optional[MTLSConfig] = None
    if auth_type == AuthType.MTLS:
        mtls = config.get("mtls", {})
        mtls_config = MTLSConfig(
            ca_cert=mtls.get("ca_cert", ""),
            client_cert=mtls.get("client_cert", ""),
            client_key=mtls.get("client_key", ""),
        )

    installation = config.get("installation", "Cloud")

    return Client(
        server=server,
        login=login,
        token=token,
        auth_type=auth_type,
        debug=debug,
        insecure=insecure,
        mtls_config=mtls_config,
        installation=installation,
    )


def get_default_client(debug: bool = False) -> Client:
    """Get default Jira client (loads config from default location)."""
    from jira_cli.internal.cmd.root import load_config

    config = load_config()

    server = config.get("server", "")
    login = config.get("login", "")
    insecure = config.get("insecure", False)

    token = os.environ.get("JIRA_API_TOKEN", "")

    auth_type_str = config.get("auth_type", "basic")
    auth_type = AuthType(auth_type_str.lower()) if auth_type_str else AuthType.BASIC

    mtls_config: Optional[MTLSConfig] = None
    if auth_type == AuthType.MTLS:
        mtls = config.get("mtls", {})
        mtls_config = MTLSConfig(
            ca_cert=mtls.get("ca_cert", ""),
            client_cert=mtls.get("client_cert", ""),
            client_key=mtls.get("client_key", ""),
        )

    installation = config.get("installation", "Cloud")

    return Client(
        server=server,
        login=login,
        token=token,
        auth_type=auth_type,
        debug=debug,
        insecure=insecure,
        mtls_config=mtls_config,
        installation=installation,
    )