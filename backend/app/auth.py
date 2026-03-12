from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# 固定用户数据
FIXED_USERS = {
    "alice": {
        "id": 1,
        "username": "alice",
        "password": "alice123",  # 简化密码
        "token": "dev_token_alice"  # 固定Token
    },
    "bob": {
        "id": 2,
        "username": "bob", 
        "password": "bob123",
        "token": "dev_token_bob"
    }
}

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    # 验证Token
    for user in FIXED_USERS.values():
        if user["token"] == token:
            return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证Token",
        headers={"WWW-Authenticate": "Bearer"},
    )

# 登录请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

# 登录响应模型  
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str