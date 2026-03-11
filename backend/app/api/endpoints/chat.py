from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ...database import get_db
from ... import models, schemas
from ...services import ai_service

router = APIRouter()
logger = logging.getLogger(__name__)

from typing import Optional
from fastapi import Body
from ...services.deletion_manager import DeletionManager

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 读取配置
MAX_BRANCH_DEPTH = int(os.getenv("BRANCH_MAX_DEPTH", "3"))
BRANCH_ONLY_AT_LATEST = os.getenv("BRANCH_ONLY_AT_LATEST", "true").lower() == "true"

# ==================== 对话管理端点 ====================

@router.post("/conversations/", response_model=schemas.Conversation)
def create_conversation(
    conversation: schemas.ConversationCreate,
    db: Session = Depends(get_db)
):
    """创建新对话"""
    try:
        # 使用默认用户ID 1（开发阶段）
        db_conversation = models.Conversation(
            title=conversation.title,
            user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        
        # 创建默认的主线程
        db_thread = models.Thread(
            conversation_id=db_conversation.id,
            title="主分支",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_thread)
        db.commit()
        
        return db_conversation
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建对话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建对话失败"
        )


@router.get("/conversations/", response_model=List[schemas.Conversation])
def read_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取对话列表（按更新时间倒序）"""
    try:
        conversations = db.query(models.Conversation)\
            .order_by(models.Conversation.updated_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        return conversations
    except Exception as e:
        logger.error(f"获取对话列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取对话列表失败"
        )


@router.get("/conversations/{conversation_id}", response_model=schemas.Conversation)
def read_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """获取对话详情"""
    db_conversation = db.query(models.Conversation)\
        .filter(models.Conversation.id == conversation_id)\
        .first()
    
    if db_conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    return db_conversation


@router.put("/conversations/{conversation_id}", response_model=schemas.Conversation)
def update_conversation(
    conversation_id: int,
    conversation: schemas.ConversationUpdate,
    db: Session = Depends(get_db)
):
    """更新对话标题"""
    db_conversation = db.query(models.Conversation)\
        .filter(models.Conversation.id == conversation_id)\
        .first()
    
    if db_conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 只更新提供的字段
    update_data = conversation.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_conversation, field, value)
    
    db_conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_conversation)
    
    return db_conversation

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    user_id: Optional[int] = Body(None, embed=True),  # 未来支持多用户
    db: Session = Depends(get_db)
):
    """
    删除对话
    """
    try:
        # 创建删除管理器
        manager = DeletionManager(db)
        
        # 执行删除
        success, message = manager.delete_conversation(conversation_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return {
            "message": message,
            "code": 200
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话端点错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请稍后重试"
        )

@router.get("/conversations/{conversation_id}/threads", response_model=List[schemas.Thread])
def get_conversation_threads(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """获取对话的所有线程"""
    # 验证对话是否存在
    conversation = db.query(models.Conversation)\
        .filter(models.Conversation.id == conversation_id)\
        .first()
    
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取对话的所有线程
    threads = db.query(models.Thread)\
        .filter(models.Thread.conversation_id == conversation_id)\
        .order_by(models.Thread.created_at.asc())\
        .all()
    
    return threads


@router.get("/conversations/{conversation_id}/thread-tree")
def get_conversation_thread_tree(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """获取对话的线程树结构，用于前端可视化"""
    # 验证对话是否存在
    conversation = db.query(models.Conversation)\
        .filter(models.Conversation.id == conversation_id)\
        .first()
    
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取对话的所有线程
    threads = db.query(models.Thread)\
        .filter(models.Thread.conversation_id == conversation_id)\
        .order_by(models.Thread.created_at.asc())\
        .all()
    
    # 构建线程映射
    thread_dict = {thread.id: thread for thread in threads}
    
    # 构建父子关系
    children = {}
    root_threads = []
    
    for thread in threads:
        if thread.parent_message_id:
            # 找到父消息所在的线程
            parent_message = db.query(models.Message)\
                .filter(models.Message.id == thread.parent_message_id)\
                .first()
            
            if parent_message:
                parent_thread_id = parent_message.thread_id
                if parent_thread_id in thread_dict:  # 确保父线程存在
                    if parent_thread_id not in children:
                        children[parent_thread_id] = []
                    children[parent_thread_id].append(thread)
                    continue
        
        # 没有父消息的线程是根节点
        root_threads.append(thread)
    
    # 递归构建树
    def build_tree(node):
        node_data = {
            "id": node.id,
            "conversation_id": node.conversation_id,
            "title": node.title or f"分支-{node.id}",
            "parent_message_id": node.parent_message_id,
            "is_active": node.is_active,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None,
            "depth": node.depth #新增
        }
        
        if node.id in children:
            node_data["children"] = [build_tree(child) for child in children[node.id]]
        else:
            node_data["children"] = []
        
        return node_data
    
    # 构建完整的树
    tree = [build_tree(thread) for thread in root_threads]
    
    return tree


# ==================== 线程管理端点 ====================

@router.get("/threads/{thread_id}", response_model=schemas.Thread)
def get_thread(
    thread_id: int,
    db: Session = Depends(get_db)
):
    """获取线程详情"""
    thread = db.query(models.Thread)\
        .filter(models.Thread.id == thread_id)\
        .first()
    
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="线程不存在"
        )
    
    return thread


@router.get("/threads/{thread_id}/messages", response_model=List[schemas.Message])
def get_thread_messages(
    thread_id: int,
    db: Session = Depends(get_db)
):
    """获取线程的所有消息"""
    # 验证线程是否存在
    thread = db.query(models.Thread)\
        .filter(models.Thread.id == thread_id)\
        .first()
    
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="线程不存在"
        )
    
    # 获取线程的所有消息
    messages = db.query(models.Message)\
        .filter(models.Message.thread_id == thread_id)\
        .order_by(models.Message.created_at.asc())\
        .all()
    
    return messages


# ==================== 消息处理端点 ====================

@router.post("/chat/", response_model=schemas.SendMessageResponse)
async def send_message(
    request: schemas.SendMessageRequest,
    db: Session = Depends(get_db)
):
    """发送消息并获取AI回复"""
    try:
        # 1. 验证线程
        thread = db.query(models.Thread).filter(models.Thread.id == request.thread_id).first()
        if not thread:
            raise HTTPException(status_code=404, detail="线程不存在")
        
        # 2. 获取父消息（用于构建消息链）
        parent_message = None
        if request.parent_id:
            parent_message = db.query(models.Message)\
                .filter(models.Message.id == request.parent_id)\
                .first()
        
        # 3. 创建用户消息
        user_message = models.Message(
            thread_id=request.thread_id,
            role="user",
            content=request.content,
            parent_id=request.parent_id,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # 4. 获取对话历史（用于上下文）
        history_messages = db.query(models.Message)\
            .filter(models.Message.thread_id == request.thread_id)\
            .order_by(models.Message.created_at.asc())\
            .all()
        
        # 构建AI消息格式
        ai_messages = []
        for msg in history_messages:
            if msg.role == "user":
                ai_messages.append({"role": "user", "content": msg.content})
            else:
                ai_messages.append({"role": "assistant", "content": msg.content})
        
        # 5. 调用AI服务
        model = request.model or "deepseek-chat"
        try:
            ai_response = ai_service.ai_service.chat_completion(
                messages=ai_messages,
                model=model
            )
        except Exception as ai_error:
            logger.error(f"AI服务调用失败: {str(ai_error)}")
            # 返回一个错误回复
            ai_response = {
                "content": f"抱歉，AI服务暂时不可用。错误: {str(ai_error)}",
                "model_used": "error",
                "tokens": 0
            }
        
        # 6. 创建AI回复消息
        ai_message = models.Message(
            thread_id=request.thread_id,
            role="assistant",
            content=ai_response["content"],
            parent_id=user_message.id,
            model_used=ai_response.get("model_used"),
            tokens=ai_response.get("tokens"),
            created_at=datetime.utcnow()
        )
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        
        # 7. 更新线程的活跃状态
        thread.is_active = True
        thread.updated_at = datetime.utcnow()
        db.commit()
        
        # 8. 返回响应
        return schemas.SendMessageResponse(
            user_message=user_message,
            ai_message=ai_message,
            conversation_id=thread.conversation_id,
            thread_id=thread.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"发送消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


# ==================== 分支创建端点 ====================

@router.post("/branch/")
async def create_branch(
    request: schemas.CreateBranchRequest,
    db: Session = Depends(get_db)
):
    """创建新的对话分支（仅限最新消息 + 深度限制）"""
    try:
        # 1. 验证对话存在
        conversation = db.query(models.Conversation)\
            .filter(models.Conversation.id == request.conversation_id)\
            .first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        # 2. 验证父消息存在
        parent_message = db.query(models.Message)\
            .filter(models.Message.id == request.parent_message_id)\
            .first()
        
        if not parent_message:
            raise HTTPException(status_code=404, detail="父消息不存在")
        
        # 3. 获取父消息所在线程
        parent_thread = db.query(models.Thread)\
            .filter(models.Thread.id == parent_message.thread_id)\
            .first()
        
        if not parent_thread:
            raise HTTPException(status_code=404, detail="父消息所在线程不存在")
        
        # ===== 新增校验1：必须是线程最新消息 =====
        # 查询该线程的最新消息
        latest_message_in_thread = db.query(models.Message)\
            .filter(models.Message.thread_id == parent_message.thread_id)\
            .order_by(models.Message.created_at.desc())\
            .first()
        
        if not latest_message_in_thread:
            raise HTTPException(status_code=400, detail="线程无消息，无法创建分支")
        
        if request.parent_message_id != latest_message_in_thread.id:
            raise HTTPException(
                status_code=400,
                detail="仅允许在当前线程的最新消息处创建分支。请切换到目标线程查看最新对话。"
            )
        # ============================================
        
        # ===== 新增校验2：深度限制 =====
        # 注意：主分支 depth=0，一级分支 depth=1，二级分支 depth=2，三级分支 depth=3（已达上限）
        if parent_thread.depth >= MAX_BRANCH_DEPTH:
            raise HTTPException(
                status_code=400,
                detail=f"分支深度已达上限（{MAX_BRANCH_DEPTH}层）。当前深度：{parent_thread.depth}层，请在更上层对话创建分支。"
            )
        # ============================================
        
        # 4. 获取父消息之前的所有消息（此时parent_message必为最新，故获取全部历史）
        thread_messages = db.query(models.Message)\
            .filter(models.Message.thread_id == parent_message.thread_id)\
            .order_by(models.Message.created_at.asc())\
            .all()
        
        # 由于校验了是最新消息，history_messages 即为完整线程历史
        history_messages = thread_messages  # 简化逻辑：直接使用全部消息
        
        # 5. 创建新线程（关键：设置 depth = 父线程 depth + 1）
        thread_title = f"分支-{parent_thread.title}" if parent_thread.title else f"分支-{parent_thread.id}"
        new_thread = models.Thread(
            conversation_id=request.conversation_id,
            parent_message_id=request.parent_message_id,
            title=thread_title,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            depth=parent_thread.depth + 1  # ===== 核心：继承父深度+1 =====
        )
        db.add(new_thread)
        db.commit()
        db.refresh(new_thread)
        
        # 6. 复制历史消息到新线程（逻辑不变）
        message_map = {}  # 用于映射旧消息ID到新消息ID
        
        for msg in history_messages:
            new_msg = models.Message(
                thread_id=new_thread.id,
                role=msg.role,
                content=msg.content,
                parent_id=message_map.get(msg.parent_id) if msg.parent_id else None,
                model_used=msg.model_used,
                tokens=msg.tokens,
                created_at=datetime.utcnow()
            )
            db.add(new_msg)
            db.commit()
            db.refresh(new_msg)
            message_map[msg.id] = new_msg.id
        
        # 7. 如果有新消息，添加到新线程（逻辑不变）
        if request.new_message_content:
            new_user_msg = models.Message(
                thread_id=new_thread.id,
                role="user",
                content=request.new_message_content,
                parent_id=message_map.get(parent_message.id),  # 父消息是新线程中的最后一个消息
                created_at=datetime.utcnow()
            )
            db.add(new_user_msg)
            db.commit()
        
        # 8. 将新线程设为活跃，其他线程设为非活跃（逻辑不变）
        db.query(models.Thread)\
            .filter(
                models.Thread.conversation_id == request.conversation_id,
                models.Thread.id != new_thread.id
            )\
            .update({"is_active": False})
        db.commit()
        
        return {
            "data": schemas.Thread.from_orm(new_thread),
            "code": 200,
            "message": "Branch created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建分支失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建分支失败: {str(e)}")