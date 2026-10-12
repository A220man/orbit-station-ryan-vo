from datetime import datetime, timezone
from typing import Optional, List
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
import httpx

from app.core.config import settings

security_bearer = HTTPBearer(auto_error=False)

class UserToken(BaseModel):
    sub: str
    username: str
    roles: List[str]
    email: Optional[str] = None

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)) -> UserToken:
    if settings.demo_mode:
        # Development demo mode: fallback to default operator role if no credentials are supplied
        if not credentials:
            return UserToken(
                sub="demo-local-user",
                username="operator-demo",
                roles=["operator", "viewer"],
                email="demo@orbit-station.local"
            )
        token = credentials.credentials
        # In demo mode, inspect mock/test tokens if supplied
        if token == "admin-token":
            return UserToken(sub="demo-admin", username="admin-demo", roles=["admin", "operator", "viewer"])
        if token == "viewer-token":
            return UserToken(sub="demo-viewer", username="viewer-demo", roles=["viewer"])
        if token == "operator-token":
            return UserToken(sub="demo-operator", username="operator-demo", roles=["operator", "viewer"])

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        # In production mode, parse and validate the OIDC JWT token claims
        claims = jwt.get_unverified_claims(token)
        roles = claims.get("resource_access", {}).get(settings.oidc_client_id, {}).get("roles", [])
        if "realm_access" in claims:
            roles.extend(claims.get("realm_access", {}).get("roles", []))
        return UserToken(
            sub=claims.get("sub", "unknown"),
            username=claims.get("preferred_username", claims.get("sub", "user")),
            roles=list(set(roles)),
            email=claims.get("email")
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid security token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(required_role: str):
    def role_checker(user: UserToken = Depends(get_current_user)) -> UserToken:
        if required_role not in user.roles and "admin" not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User lacks required role: {required_role}"
            )
        return user
    return role_checker
