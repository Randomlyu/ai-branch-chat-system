from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import chat
from .database import engine
from . import models

from .auth import LoginRequest, LoginResponse, FIXED_USERS, get_current_user

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI分支对话系统API",
    description="支持分支对话的AI聊天系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由器 - 这是关键，确保只有一个路由器
app.include_router(chat.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "AI分支对话系统API"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

# 登录端点
@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    user = FIXED_USERS.get(login_data.username)
    
    if not user or user["password"] != login_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    return LoginResponse(
        access_token=user["token"],
        user_id=user["id"],
        username=user["username"]
    )

# 健康检查端点（无需认证）
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 受保护的测试端点
@app.get("/api/v1/auth/test")
async def test_auth(current_user: dict = Depends(get_current_user)):
    return {
        "message": f"你好, {current_user['username']}!",
        "user_id": current_user["id"]
    }