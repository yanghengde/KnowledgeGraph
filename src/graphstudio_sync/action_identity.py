"""Server-derived identity boundary for governed Camstar actions."""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from fastapi import HTTPException, Request

from .config import SyncSettings


@dataclass(frozen=True)
class ActionPrincipal:
    subject: str
    roles: tuple[str, ...]
    authenticated: bool


def action_principal(request: Request, settings: SyncSettings) -> ActionPrincipal:
    mode = settings.action_auth_mode
    if mode == "disabled":
        return ActionPrincipal("local-preview", (), False)
    if mode != "trusted_headers":
        raise HTTPException(status_code=503, detail=f"Unsupported ACTION_AUTH_MODE: {mode}")
    configured_secret = settings.action_trusted_proxy_secret or ""
    supplied_secret = request.headers.get("x-action-proxy-secret", "")
    if not configured_secret or not hmac.compare_digest(configured_secret, supplied_secret):
        raise HTTPException(status_code=401, detail="Trusted Action identity is missing")
    subject = request.headers.get("x-authenticated-user", "").strip()
    roles = tuple(sorted({
        value.strip() for value in request.headers.get("x-authenticated-roles", "").split(",")
        if value.strip()
    }))
    if not subject:
        raise HTTPException(status_code=401, detail="Authenticated Action user is missing")
    return ActionPrincipal(subject, roles, True)


def require_action_principal(principal: ActionPrincipal) -> None:
    if not principal.authenticated:
        raise HTTPException(
            status_code=403,
            detail="Real Actions require ACTION_AUTH_MODE=trusted_headers and a trusted proxy identity",
        )
