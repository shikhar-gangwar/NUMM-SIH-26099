from datetime import timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import AppUser
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.core.errors import UnauthorizedException
from app.api.schemas.user import UserLoginRequest, TokenDTO, UserDTO
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenDTO)
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(AppUser).filter_by(username=req.username, is_active=True).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise UnauthorizedException("Invalid username or password")
    
    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "cpse_id": user.cpse_id
    })
    
    user_dto = UserDTO(
        id=user.id,
        username=user.username,
        role=user.role,
        cpse_id=user.cpse_id,
        is_active=user.is_active
    )
    return TokenDTO(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TTL_MIN * 60,
        user=user_dto
    )

@router.get("/me", response_model=UserDTO)
def get_me(current_user: AppUser = Depends(get_current_user)):
    return UserDTO(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        cpse_id=current_user.cpse_id,
        is_active=current_user.is_active
    )
