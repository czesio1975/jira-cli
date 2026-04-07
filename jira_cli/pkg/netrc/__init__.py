"""Netrc file reader.

Compatible with Go version's netrc handling.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class NetrcEntry:
    """Netrc entry."""

    machine: str
    login: str
    password: str


def read_netrc(server: str, login: str) -> Optional[NetrcEntry]:
    """Read credentials from .netrc file.

    Args:
        server: Jira server hostname
        login: Login username/email

    Returns:
        NetrcEntry if found, None otherwise
    """
    # Extract hostname from server URL
    from urllib.parse import urlparse
    parsed = urlparse(server)
    hostname = parsed.hostname or server

    # Find .netrc file
    netrc_path = Path.home() / ".netrc"

    # Also check _netrc on Windows
    if not netrc_path.exists():
        netrc_path = Path.home() / "_netrc"

    if not netrc_path.exists():
        return None

    try:
        import netrc
        netrc_file = netrc.netrc(str(netrc_path))

        # Try exact hostname match
        auth = netrc_file.authenticators(hostname)
        if auth:
            netrc_login, _, password = auth
            if netrc_login and password:
                return NetrcEntry(machine=hostname, login=netrc_login, password=password)

        # Try matching by login
        for machine in netrc_file.hosts:
            entry_login, _, password = netrc_file.hosts[machine]
            if entry_login == login and password:
                return NetrcEntry(machine=machine, login=login, password=password)

    except (FileNotFoundError, KeyError):
        pass

    return None