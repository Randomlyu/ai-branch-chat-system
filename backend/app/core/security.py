# backend/app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
import hashlib
import bcrypt

load_dotenv()

# 安全配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # 2小时
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7天

# 密码工具
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        # 尝试使用bcrypt验证
        if hashed_password.startswith("$2"):  # bcrypt哈希格式
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:
            # 回退到sha256验证
            return hashed_password == get_password_hash_simple(plain_password)
    except Exception as e:
        print(f"密码验证错误: {e}")
        return False

def get_password_hash(password: str) -> str:
    """生成密码哈希 - 主方法"""
    try:
        # 尝试使用bcrypt
        # 确保密码是字节，长度不超过72
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"bcrypt哈希失败，使用回退方法: {e}")
        # 回退到sha256
        return get_password_hash_simple(password)

def get_password_hash_simple(password: str) -> str:
    """简化版密码哈希（仅用于开发）"""
    # 添加盐值
    salt = "your-salt-string-change-in-production"
    return hashlib.sha256((password + salt).encode()).hexdigest()

# JWT工具
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None