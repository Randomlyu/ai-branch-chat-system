from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from .api.endpoints import chat, auth
from .database import engine, get_db
from . import models
from .models import User
from .core.security import get_password_hash
from .auth import get_current_user

# 加载环境变量
load_dotenv()

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

# 初始化15个用户
def init_users():
    """初始化15个用户"""
    db = next(get_db())
    try:
        for i in range(1, 16):
            username = f"user{i}"
            email = f"user{i}@example.com"
            
            # 检查用户是否已存在
            existing_user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if not existing_user:
                user = User(
                    username=username,
                    email=email,
                    hashed_password=get_password_hash("123456"),  # 初始密码
                    is_active=True,
                    need_password_change=True
                )
                db.add(user)
                print(f"✅ 创建用户: {username}")
        
        db.commit()
        print("✅ 用户初始化完成")
    except Exception as e:
        print(f"❌ 用户初始化失败: {e}")
        db.rollback()
    finally:
        db.close()

# 应用启动时初始化用户
init_users()

app = FastAPI(
    title="AI分支对话系统API",
    description="支持分支对话的AI聊天系统",
    version="3.0"
)

# 配置CORS
# 从环境变量读取允许的源，支持多个域名用逗号分隔
origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
origins = [origin.strip() for origin in origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print(f"✅ CORS允许的域名: {origins}")

# 包含路由器
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(chat.router, prefix="/api/v1", tags=["聊天"])

@app.get("/")
async def root():
    return {"message": "AI分支对话系统API"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/auth/test")
async def test_auth(current_user: User = Depends(get_current_user)):
    """测试认证端点"""
    return {
        "message": f"你好, {current_user.username}!",
        "user_id": current_user.id,
        "username": current_user.username
    }