from pydantic import BaseModel
from typing import Optional

class UserLoginRequest(BaseModel):
    username: str
    password: str

class TokenDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserDTO"

class UserDTO(BaseModel):
    id: str
    username: str
    role: str
    cpse_id: Optional[str] = None
    is_active: bool

TokenDTO.model_rebuild()
