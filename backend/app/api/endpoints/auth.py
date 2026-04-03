from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta, timezone

from ...database import get_db
from ...models import User
from ...core.security import (
    verify_password, get_password_hash, 
    create_access_token, create_refresh_token, verify_token
)
from ...auth import validate_password, validate_username, get_current_user
from ...schemas import (
    LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse,
    ChangePasswordRequest, ChangePasswordResponse, UserInfo
)

router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录
    """
    # 查找用户
    user = db.query(User).filter(
        (User.username == login_data.username) | 
        (User.email == login_data.username)
    ).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 验证密码
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 生成令牌
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        username=user.username,
        need_password_change=user.need_password_change
    )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌
    """
    # 验证刷新令牌
    payload = verify_token(refresh_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌"
        )
    
    # 检查用户是否存在且激活
    user = db.query(User).filter(
        User.id == int(user_id),
        User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    # 生成新的访问令牌
    token_data = {"sub": str(user.id)}
    new_access_token = create_access_token(data=token_data)
    
    return RefreshTokenResponse(
        access_token=new_access_token
    )

@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    """
    # 验证当前密码
    if not verify_password(change_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 验证新密码
    validate_password(change_data.new_password)
    
    # 新密码不能与旧密码相同
    if verify_password(change_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与当前密码相同"
        )
    
    # 更新密码
    current_user.hashed_password = get_password_hash(change_data.new_password)
    current_user.need_password_change = False
    current_user.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return ChangePasswordResponse(
        code=200,
        message="密码修改成功"
    )

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return current_user