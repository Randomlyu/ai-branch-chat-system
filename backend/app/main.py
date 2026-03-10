from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import chat
from .database import engine
from . import models

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