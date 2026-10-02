from typing import List, Callable
from fastapi import Depends, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import AppUser
from app.core.security import decode_access_token
from app.core.errors import UnauthorizedException, ForbiddenException

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> AppUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    
    username = payload.get("sub")
    if not username:
        raise UnauthorizedException("Invalid token claims")
    
    user = db.query(AppUser).filter_by(username=username, is_active=True).first()
    if not user:
        raise UnauthorizedException("User not found or inactive")
    
    return user

def require_role(allowed_roles: List[str]) -> Callable:
    def role_checker(current_user: AppUser = Depends(get_current_user)) -> AppUser:
        if current_user.role not in allowed_roles and current_user.role != "SUPER_ADMIN":
            raise ForbiddenException(f"Role '{current_user.role}' not permitted for this action")
        return current_user
    return role_checker
