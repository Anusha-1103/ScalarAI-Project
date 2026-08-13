from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header
from jwt import PyJWKClient

from app.common.exceptions import ApplicationError
from app.common.settings_config import get_settings


@dataclass(frozen=True)
class CurrentPrincipal:
    auth_user_id: str | None
    email: str
    display_name: str


@lru_cache
def get_jwk_client(url: str) -> PyJWKClient:
    return PyJWKClient(f"{url.rstrip('/')}/auth/v1/.well-known/jwks.json", cache_jwk_set=True)


def _decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"  # type: ignore[union-attr]
    try:
        if settings.supabase_jwt_secret:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=issuer,
            )
        key = get_jwk_client(settings.supabase_url or "").get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            key.key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
            issuer=issuer,
        )
    except jwt.PyJWTError as error:
        raise ApplicationError(
            "INVALID_SESSION", "Your session is invalid or expired", 401
        ) from error


async def get_current_principal(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentPrincipal:
    settings = get_settings()
    if not settings.auth_enabled:
        return CurrentPrincipal(None, "anusha@echonote.local", "Anusha")
    if not authorization or not authorization.startswith("Bearer "):
        raise ApplicationError("AUTHENTICATION_REQUIRED", "Please sign in to continue", 401)
    claims = _decode_token(authorization.removeprefix("Bearer ").strip())
    metadata = claims.get("user_metadata") or {}
    email = str(claims.get("email") or "")
    return CurrentPrincipal(
        auth_user_id=str(claims["sub"]),
        email=email,
        display_name=str(metadata.get("full_name") or metadata.get("name") or email.split("@")[0]),
    )


CurrentPrincipalDependency = Annotated[CurrentPrincipal, Depends(get_current_principal)]
