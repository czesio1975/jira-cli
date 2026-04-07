"""JIRA API client.

Converted from pkg/jira/client.go
"""

import json
import logging
import ssl
from pathlib import Path
from typing import Dict, Any, Optional

import httpx

from jira_cli.pkg.jira.types import (
    AuthType,
    MTLSConfig,
)

logger = logging.getLogger(__name__)

# Constants
CLIENT_TIMEOUT = 30.0
BASE_URL_V3 = "/rest/api/3"
BASE_URL_V2 = "/rest/api/2"
BASE_URL_V1 = "/rest/agile/1.0"


class JiraError(Exception):
    """Base Jira error."""

    pass


class EmptyResponseError(JiraError):
    """Empty response from server."""

    pass


class UnexpectedResponseError(JiraError):
    """Unexpected response from server."""

    def __init__(self, status_code: int, status: str, body: Dict[str, Any]) -> None:
        self.status_code = status_code
        self.status = status
        self.body = body
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        msg = []
        if error_messages := self.body.get("errorMessages", []):
            msg.append("\nError:")
            for em in error_messages:
                msg.append(f"  - {em}")
        if errors := self.body.get("errors", {}):
            msg.append("\nError:")
            for k, v in errors.items():
                msg.append(f"  - {k}: {v}")
        if warning_messages := self.body.get("warningMessages", []):
            msg.append("\nWarning:")
            for wm in warning_messages:
                msg.append(f"  - {wm}")
        return "\n".join(msg)


class Client:
    """JIRA API client."""

    def __init__(
        self,
        server: str,
        login: str,
        token: str,
        auth_type: AuthType = AuthType.BASIC,
        insecure: bool = False,
        debug: bool = False,
        mtls_config: Optional[MTLSConfig] = None,
        timeout: float = CLIENT_TIMEOUT,
        installation: str = "Cloud",
    ) -> None:
        self.server = server.rstrip("/")
        self.login = login
        self.token = token
        self.auth_type = auth_type
        self.insecure = insecure
        self.debug = debug
        self.timeout = timeout
        self.installation = installation
        self._client: Optional[httpx.Client] = None
        self._mtls_config = mtls_config

    @property
    def default_api_version(self) -> str:
        """Return the default REST API version based on installation type."""
        return "v3" if self.installation == "Cloud" else "v2"

    def _create_client(self) -> httpx.Client:
        """Create HTTP client with proper configuration."""
        # Base transport settings
        transport = None

        # SSL/TLS configuration
        ssl_context: Optional[ssl.SSLContext] = None
        if self.insecure:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        # mTLS configuration
        if self.auth_type == AuthType.MTLS and self._mtls_config:
            ca_cert_path = Path(self._mtls_config.ca_cert)
            client_cert_path = Path(self._mtls_config.client_cert)
            client_key_path = Path(self._mtls_config.client_key)

            if ca_cert_path.exists() and client_cert_path.exists() and client_key_path.exists():
                ssl_context = ssl.create_default_context(cafile=str(ca_cert_path))
                ssl_context.load_cert_chain(str(client_cert_path), str(client_key_path))

        # Build client
        kwargs: Dict[str, Any] = {
            "base_url": self.server,
            "timeout": self.timeout,
            "verify": ssl_context if ssl_context else True,
        }

        # Set authentication
        if self.auth_type == AuthType.BASIC:
            kwargs["auth"] = (self.login, self.token)
        elif self.auth_type == AuthType.BEARER:
            kwargs["headers"] = {"Authorization": f"Bearer {self.token}"}
        elif self.auth_type == AuthType.MTLS and self.token:
            kwargs["headers"] = {"Authorization": f"Bearer {self.token}"}

        return httpx.Client(**kwargs)

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _request(
        self,
        method: str,
        path: str,
        api_version: str = "v3",
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to Jira API."""
        # Build URL path
        if api_version == "v3":
            url = f"{BASE_URL_V3}{path}"
        elif api_version == "v2":
            url = f"{BASE_URL_V2}{path}"
        else:
            url = f"{BASE_URL_V1}{path}"

        # Build headers
        req_headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        # Bearer auth header (if needed)
        if self.auth_type == AuthType.BEARER:
            req_headers["Authorization"] = f"Bearer {self.token}"

        if self.debug:
            logger.debug("Request: %s %s", method, url)
            if body:
                logger.debug("Body: %s", json.dumps(body, indent=2))

        try:
            response = self.client.request(
                method=method,
                url=url,
                json=body,
                params=params,
                headers=req_headers,
            )

            if self.debug:
                logger.debug("Response: %d", response.status_code)
                logger.debug("Body: %s", response.text[:500])

            # Handle responses
            if response.status_code in (200, 201):
                return response.json() if response.content else {}
            elif response.status_code == 204:
                return {}
            else:
                try:
                    error_body = response.json()
                except json.JSONDecodeError:
                    error_body = {"errorMessages": [response.text]}
                raise UnexpectedResponseError(
                    status_code=response.status_code,
                    status=response.reason_phrase,
                    body=error_body,
                )

        except httpx.HTTPStatusError as e:
            try:
                error_body = e.response.json()
            except json.JSONDecodeError:
                error_body = {"errorMessages": [str(e)]}
            raise UnexpectedResponseError(
                status_code=e.response.status_code,
                status=e.response.reason_phrase,
                body=error_body,
            )

    # HTTP method helpers
    def get(
        self,
        path: str,
        api_version: str = "v3",
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """GET request."""
        return self._request("GET", path, api_version=api_version, params=params, headers=headers)

    def post(
        self,
        path: str,
        body: Dict[str, Any],
        api_version: str = "v3",
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """POST request."""
        return self._request("POST", path, api_version=api_version, body=body, headers=headers)

    def put(
        self,
        path: str,
        body: Dict[str, Any],
        api_version: str = "v3",
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """PUT request."""
        return self._request("PUT", path, api_version=api_version, body=body, headers=headers)

    def delete(
        self,
        path: str,
        api_version: str = "v2",
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """DELETE request."""
        return self._request("DELETE", path, api_version=api_version, params=params, headers=headers)

    # Convenience methods for API versions
    def get_v2(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request to v2 API."""
        return self.get(path, api_version="v2", params=params)

    def get_v1(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request to v1 API."""
        return self.get(path, api_version="v1", params=params)

    def post_v2(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """POST request to v2 API."""
        return self.post(path, body, api_version="v2")

    def post_v1(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """POST request to v1 API."""
        return self.post(path, body, api_version="v1")

    def put_v2(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """PUT request to v2 API."""
        return self.put(path, body, api_version="v2")

    def put_v1(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """PUT request to v1 API."""
        return self.put(path, body, api_version="v1")

    def post_raw(
        self,
        path: str,
        content: str,
        api_version: str = "v3",
    ) -> Dict[str, Any]:
        """POST request with a raw string body (e.g. for watchers API)."""
        if api_version == "v3":
            url = f"{BASE_URL_V3}{path}"
        elif api_version == "v2":
            url = f"{BASE_URL_V2}{path}"
        else:
            url = f"{BASE_URL_V1}{path}"

        req_headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.auth_type == AuthType.BEARER:
            req_headers["Authorization"] = f"Bearer {self.token}"

        response = self.client.request(
            method="POST",
            url=url,
            content=content,
            headers=req_headers,
        )
        if response.status_code in (200, 201):
            return response.json() if response.content else {}
        elif response.status_code == 204:
            return {}
        else:
            try:
                error_body = response.json()
            except json.JSONDecodeError:
                error_body = {"errorMessages": [response.text]}
            raise UnexpectedResponseError(
                status_code=response.status_code,
                status=response.reason_phrase,
                body=error_body,
            )

    def close(self) -> None:
        """Close the client."""
        if self._client:
            self._client.close()
            self._client = None