import os
import re

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


def load_service_auth_secret() -> str:
    secret = os.environ.get("AICA_BACKEND_SECRET", "")

    if re.fullmatch(r"[0-9a-f]{64}", secret) is None:
        raise RuntimeError(
            "AICA_BACKEND_SECRET must contain 64 lowercase hex characters."
        )

    return secret


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Invalid service authentication",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_service_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    if credentials is None:
        raise unauthorized()

    try:
        claims = jwt.decode(
            credentials.credentials,
            request.app.state.service_auth_secret,
            algorithms=["HS256"],
            issuer="aica-shopware",
            audience="aica-backend",
            leeway=5,
            options={
                "require": [
                    "iss",
                    "aud",
                    "sub",
                    "token_use",
                    "iat",
                    "exp",
                ],
            },
        )

        if claims["sub"] != "shopware-proxy":
            raise jwt.InvalidTokenError("Invalid service subject")

        if claims["token_use"] != "service":
            raise jwt.InvalidTokenError("Invalid token purpose")

        issued_at = claims["iat"]
        expires_at = claims["exp"]

        if type(issued_at) is not int or type(expires_at) is not int:
            raise jwt.InvalidTokenError("Invalid timestamp type")

        if not 0 < expires_at - issued_at <= 60:
            raise jwt.InvalidTokenError("Invalid token lifetime")

    except jwt.InvalidTokenError:
        raise unauthorized() from None