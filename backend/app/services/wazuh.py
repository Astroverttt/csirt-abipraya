"""
Async Wazuh API client.

Handles authentication, token refresh, and all Wazuh API calls.
Credentials are passed from the session store (never hardcoded).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from ..config import settings

logger = logging.getLogger("patchops.wazuh")

# ── Per-session Wazuh token cache ─────────────────────────────────────────────
_wazuh_tokens: Dict[str, str] = {}


def _client(verify: bool = False) -> httpx.AsyncClient:
    """Create a new httpx client with appropriate SSL settings."""
    return httpx.AsyncClient(
        base_url=settings.WAZUH_API_URL,
        verify=verify if settings.WAZUH_VERIFY_SSL else False,
        timeout=httpx.Timeout(15.0),
    )


async def authenticate(username: str, password: str) -> str:
    """
    Authenticate a specific user against Wazuh API.
    Used for the initial login validation.
    """
    import base64
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

    async with _client() as client:
        try:
            response = await client.post(
                "/security/user/authenticate",
                headers={"Authorization": f"Basic {credentials}"},
            )
            if response.status_code == 401:
                logger.warning("Wazuh Login Failed: Unauthorized for user %s", username)
                return ""
            
            response.raise_for_status()
            token = response.json().get("data", {}).get("token")
            return token
        except httpx.ConnectError:
            logger.error("Wazuh Connection Failed: Cannot reach %s", settings.WAZUH_API_URL)
            raise Exception(f"Cannot reach Wazuh API at {settings.WAZUH_API_URL}")
        except Exception as e:
            logger.error("Wazuh Auth Error: %s", e)
            raise e


async def get_token(session_id: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None) -> str:
    """Get or refresh the Wazuh API token for a session or the system account."""
    # CASE 1: Use Static Service Account if configured in .env
    if settings.WAZUH_API_USERNAME and settings.WAZUH_API_PASSWORD:
        key = "__SYSTEM__"
        cached = _wazuh_tokens.get(key)
        if cached: return cached
        
        logger.info("Authenticating with Static Wazuh Credentials (%s)...", settings.WAZUH_API_USERNAME)
        token = await authenticate(settings.WAZUH_API_USERNAME, settings.WAZUH_API_PASSWORD)
        if token:
            _wazuh_tokens[key] = token
            return token

    # CASE 2: Fallback to Session-based User (provided during login)
    if not session_id:
        raise ValueError("No session_id and no static credentials configured")

    cached = _wazuh_tokens.get(session_id)
    if cached: return cached

    if not username or not password:
        raise ValueError(f"Session {session_id} expired and no credentials provided to refresh")

    token = await authenticate(username, password)
    if token:
        _wazuh_tokens[session_id] = token
    return token


def invalidate_token(session_id: str) -> None:
    """Remove cached token for a session."""
    _wazuh_tokens.pop(session_id, None)


async def api_request(
    session_id: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    method: str = "GET",
    path: str = "/",
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Make an authenticated request to the Wazuh API.
    Automatically refreshes the token on 401.
    """
    token = await get_token(session_id, username, password)

    async with _client() as client:
        response = await client.request(
            method,
            path,
            params=params,
            json=json_body,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Token expired — refresh and retry once
        if response.status_code == 401:
            key = "__SYSTEM__" if (settings.WAZUH_API_USERNAME and settings.WAZUH_API_PASSWORD) else session_id
            logger.info("Wazuh token expired for %s, refreshing...", key)
            _wazuh_tokens.pop(key, None)
            
            u = settings.WAZUH_API_USERNAME or username
            p = settings.WAZUH_API_PASSWORD or password
            
            token = await authenticate(u, p)
            if token:
                _wazuh_tokens[key] = token

                response = await client.request(
                    method,
                    path,
                    params=params,
                    json=json_body,
                    headers={"Authorization": f"Bearer {token}"},
                )

        response.raise_for_status()
        return response.json()
