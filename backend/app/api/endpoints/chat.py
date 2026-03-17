from typing import List, Dict, Any, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os
import json
from dotenv import load_dotenv

from ...database import get_db
from ... import models, schemas
from ...services import ai_service
from ...services.deletion_manager import DeletionManager
# 从新的auth模块导入认证依赖
from ...auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 读取配置
MAX_BRANCH_DEPTH = int(os.getenv("BRANCH_MAX_DEPTH", "3"))
BRANCH_ONLY_AT_LATEST = os.getenv("BRANCH_ONLY_AT_LATEST", "true").lower() == "true"

# ==================== 对话管理端点 ====================

@router.post("/conversations/", response_model=schemas.Conversation)
def create_conversation(
    conversation: schemas.ConversationCreate,
    current_user: dict = Depends(get_current_user),  # 添加认证
    db: Session = Depends(get_db)
):
    """创建新对话"""
    try:
        # 使用认证用户ID
        db_conversation = models.Conversation(
            title=conversation.title,
            user_id=current_user["id"],  # 使用认证用户ID
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        
        # 创建默认的主线程
        db_thread = models.Thread(
            conversation_id=db_conversation.id,
            title="主对话",  # 修改为"主对话"更友好
            is_active=True,
            depth=0,  # 主线程深度为0
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
    current_user: dict = Depends(get_current_user),  # 添加认证
    db: Session = Depends(get_db)
):
    """获取当前用户的对话列表（按更新时间倒序）"""
    try:
        conversations = (
           db.query(models.Conversation)
           .filter(models.Conversation.user_id == current_user["id"])  # 只返回当前用户的对话
           .order_by(models.Conversation.updated_at.desc())
           .offset(skip)
           .limit(limit)
           .all()
        )
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
    current_user: dict = Depends(get_current_user),  # 添加认证
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
    
    # 验证所有权
    if db_conversation.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此对话"
        )
    
    return db_conversation


@router.put("/conversations/{conversation_id}", response_model=schemas.Conversation)
def update_conversation(
    conversation_id: int,
    conversation: schemas.ConversationUpdate,
    current_user: dict = Depends(get_current_user),  # 添加认证
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
    
    # 验证所有权
    if db_conversation.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此对话"
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
    current_user: dict = Depends(get_current_user),  # 添加认证
    db: Session = Depends(get_db)
):
    """
    删除对话
    """
    try:
        # 验证对话存在和所有权
        conversation = db.query(models.Conversation)\
            .filter(models.Conversation.id == conversation_id)\
            .first()
        
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
        
        if conversation.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此对话"
            )
        
        # 创建删除管理器
        manager = DeletionManager(db)
        
        # 执行删除
        success, message = manager.delete_conversation(conversation_id, current_user["id"])
        
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
    current_user: dict = Depends(get_current_user),  # 添加认证
    db: Session = Depends(get_db)
):
    """获取对话的所有线程"""
    # 验证对话是否存在和所有权
    conversation = db.query(models.Conversation)\
        .filter(models.Conversation.id == conversation_id)\
        .first()
    
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    if conversation.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此对话"
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
    current_user: dict = Depends(get_current_user),  # 添加认证
    db: Session = Depends(get_db)
):
    """获取对话的线程树结构，用于前端可视化"""
    # 验证对话是否存在和所有权
    conversation = db.query(models.Conversation)\
        .filter(models.Conversation.id == conversation_id)\
        .first()
    
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    if conversation.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此对话"
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
            "depth": node.depth
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
    current_user: dict = Depends(get_current_user),  # 添加认证
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
    
    # 验证对话所有权
    conversation = db.query(models.Conversation)\
        .filter(models.Conversation.id == thread.conversation_id)\
        .first()
    
    if conversation and conversation.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此线程"
        )
    
    return thread

@router.put("/threads/{thread_id}", response_model=schemas.Thread)
def update_thread_title(
    thread_id: int,
    thread_update: schemas.ThreadUpdate,  # 需要创建这个Pydantic模型
    current_user: dict = Depends(get_current_user),  # 添加认证
    db: Session = Depends(get_db)
):
    """更新线程标题"""
    thread = db.query(models.Thread)\
        .filter(models.Thread.id == thread_id)\
        .first()
    
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="线程不存在"
        )
    
    # 验证对话所有权
    conversation = db.query(models.Conversation)\
        .filter(models.Conversation.id == thread.conversation_id)\
        .first()
    
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    if conversation.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此线程"
        )
    
    # 更新标题
    thread.title = thread_update.title
    thread.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(thread)
    
    return thread


@router.get("/threads/{thread_id}/messages", response_model=List[schemas.Message])
def get_thread_messages(
    thread_id: int,
    current_user: dict = Depends(get_current_user),  # 添加认证
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
    
    # 验证对话所有权
    conversation = db.query(models.Conversation)\
        .filter(models.Conversation.id == thread.conversation_id)\
        .first()
    
    if conversation and conversation.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此线程"
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
    current_user: dict = Depends(get_current_user),  # 添加认证
    db: Session = Depends(get_db)
):
    """发送消息并获取AI回复（非流式版本）"""
    try:
        # 1. 验证线程
        thread = db.query(models.Thread).filter(models.Thread.id == request.thread_id).first()
        if not thread:
            raise HTTPException(status_code=404, detail="线程不存在")
        
        # 验证对话所有权
        conversation = db.query(models.Conversation)\
            .filter(models.Conversation.id == thread.conversation_id)\
            .first()
        
        if conversation and conversation.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="无权在此对话中发送消息")
        
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
        
        # 5. 调用AI服务（非流式）
        model = request.model
        try:
            # 使用异步版本的chat_completion
            ai_response = await ai_service.chat_completion(
                messages=ai_messages,
                model=model,
                stream=False,
                user_id=current_user["username"]  # 传递用户名作为用户标识
            )
        except ValueError as e:
            # 处理Token用量上限错误
            logger.warning(f"AI服务调用被限制: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e)
            )
        except Exception as ai_error:
            logger.error(f"AI服务调用失败: {str(ai_error)}")
            # 返回一个错误回复
            ai_response = {
                "content": f"抱歉，AI服务暂时不可用。错误: {str(ai_error)}",
                "model_used": "error",
                "tokens": 0,
                "is_streaming": False
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


@router.post("/chat/stream/")
async def send_message_stream(
    request: schemas.SendMessageRequest,
    current_user: dict = Depends(get_current_user),  # 添加认证
    db: Session = Depends(get_db)
):
    """发送消息并获取AI回复（流式版本）"""
    async def event_generator():
        try:
            # 1. 验证线程
            thread = db.query(models.Thread).filter(models.Thread.id == request.thread_id).first()
            if not thread:
                error_data = json.dumps({
                    "content": "线程不存在",
                    "error": True,
                    "done": True
                })
                yield f"data: {error_data}\n\n"
                return
            
            # 验证对话所有权
            conversation = db.query(models.Conversation)\
                .filter(models.Conversation.id == thread.conversation_id)\
                .first()
            
            if conversation and conversation.user_id != current_user["id"]:
                error_data = json.dumps({
                    "content": "无权在此对话中发送消息",
                    "error": True,
                    "done": True
                })
                yield f"data: {error_data}\n\n"
                return
            
            # 2. 获取父消息
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
            
            # 4. 获取对话历史
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
            
            # 5. 调用AI流式服务
            model = request.model
            ai_response_content = ""
            
            # 生成流式响应
            stream_generator = ai_service.stream_chat_completion(
                messages=ai_messages,
                model=model,
                user_id=current_user["username"]  # 传递用户名作为用户标识
            )
            
            async for chunk in stream_generator:
                yield chunk
                
                # 解析chunk以获取内容
                if chunk.startswith("data: "):
                    try:
                        data_str = chunk[6:]  # 移除"data: "前缀
                        if data_str.strip():  # 避免空字符串
                            data = json.loads(data_str.strip())
                            if "content" in data and not data.get("done") and not data.get("error"):
                                ai_response_content += data["content"]
                    except json.JSONDecodeError:
                        pass
            
            # 6. 创建AI回复消息
            ai_message = models.Message(
                thread_id=request.thread_id,
                role="assistant",
                content=ai_response_content,
                parent_id=user_message.id,
                model_used=model or ai_service.get_default_model(),
                created_at=datetime.utcnow()
            )
            db.add(ai_message)
            db.flush()  # 刷新以获取消息ID，但不提交事务

            # 7. 更新线程的活跃状态
            thread.is_active = True
            thread.updated_at = datetime.utcnow()

            db.commit()

            # 8. 发送包含消息ID的最后一个chunk
            message_data = json.dumps({
                "content": "",
                "done": True,
                "message_id": ai_message.id,
                "user_message_id": user_message.id,
                "model_used": model or ai_service.get_default_model()
            })
            yield f"data: {message_data}\n\n"
            
        except HTTPException as e:
            error_data = json.dumps({
                "content": f"HTTP错误: {e.detail}",
                "error": True,
                "done": True
            })
            yield f"data: {error_data}\n\n"
        except Exception as e:
            logger.error(f"流式发送消息失败: {str(e)}")
            error_data = json.dumps({
                "content": f"服务器错误: {str(e)}",
                "error": True,
                "done": True
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 防止nginx缓冲
        }
    )


@router.post("/chat/stop/")
async def stop_generation(
    current_user: dict = Depends(get_current_user)
):
    """停止当前用户的流式生成"""
    try:
        ai_service.stop_user_request(current_user["username"])
        return {
            "code": 200,
            "message": "已发送停止请求",
            "data": None
        }
    except Exception as e:
        logger.error(f"停止生成失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止生成失败: {str(e)}"
        )

@router.delete("/threads/{thread_id}/messages/{message_id}", response_model=schemas.DeleteMessageResponse)
def delete_message(
    thread_id: int,
    message_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除消息对（AI消息 + 对应的用户消息）
    注意：只能删除AI消息，会自动删除对应的用户消息
    """
    try:
        # 1. 验证线程存在
        thread = db.query(models.Thread).filter(
            models.Thread.id == thread_id
        ).first()
        
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="线程不存在"
            )
        
        # 2. 验证对话所有权
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == thread.conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
        
        if conversation.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此线程中的消息"
            )
        
        # 3. 验证消息存在且属于该线程
        message = db.query(models.Message).filter(
            models.Message.id == message_id,
            models.Message.thread_id == thread_id
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="消息不存在或不属于此线程"
            )
        
        # 4. 创建删除管理器并执行删除
        manager = DeletionManager(db)
        success, message_text, delete_info = manager.delete_message_pair(
            message_id, 
            current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message_text
            )
        
        return {
            "code": 200,
            "message": message_text,
            "data": delete_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除消息端点错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )

@router.post("/threads/{thread_id}/messages/{message_id}/regenerate", response_model=schemas.RegenerateMessageResponse)
async def regenerate_message(
    thread_id: int,
    message_id: int,
    request: schemas.RegenerateMessageRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重新生成AI消息
    规则：1. 必须是AI消息 2. 必须是最新消息 3. 不能被分支引用
    """
    try:
        # 1. 创建删除管理器
        manager = DeletionManager(db)
        
        # 2. 验证是否可以重新生成
        can_regenerate, message_text, regenerate_info = manager.regenerate_message(
            ai_message_id=message_id,
            model=request.model,
            stream=request.stream,
            user_id=current_user["id"]
        )
        
        if not can_regenerate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message_text
            )
        
        # 3. 获取原消息信息
        old_ai_message = db.query(models.Message).filter(
            models.Message.id == message_id
        ).first()
        
        if not old_ai_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="原消息不存在"
            )
        
        # 4. 获取对应的用户消息
        user_message = db.query(models.Message).filter(
            models.Message.id == old_ai_message.parent_id
        ).first()
        
        if not user_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户消息不存在"
            )
        
        # 5. 获取历史消息
        history_messages = db.query(models.Message).filter(
            models.Message.thread_id == thread_id,
            models.Message.created_at <= user_message.created_at
        ).order_by(models.Message.created_at.asc()).all()
        
        # 构建AI消息格式
        ai_messages = []
        for msg in history_messages:
            if msg.role == "user":
                ai_messages.append({"role": "user", "content": msg.content})
            else:
                ai_messages.append({"role": "assistant", "content": msg.content})
        
        # 6. 调用AI服务
        model_to_use = request.model or old_ai_message.model_used
        
        if request.stream:
            # 流式响应
            async def stream_generator():
                new_ai_message = None
                new_content = ""
                
                try:
                    # 注意：不要在生成器开始时立即删除旧消息
                    # 先获取所有必要信息
                    old_message_id = old_ai_message.id
                    old_message_content = old_ai_message.content
                    user_message_id = user_message.id
                    
                    # 调用AI流式服务
                    stream_generator = ai_service.stream_chat_completion(
                        messages=ai_messages,
                        model=model_to_use,
                        user_id=current_user["username"]
                    )
                    
                    # 流式生成内容
                    async for chunk in stream_generator:
                        yield chunk
                        
                        # 解析chunk以获取内容
                        if chunk.startswith("data: "):
                            try:
                                data_str = chunk[6:]  # 移除"data: "前缀
                                if data_str.strip():
                                    data = json.loads(data_str.strip())
                                    if "content" in data and not data.get("done") and not data.get("error"):
                                        new_content += data["content"]
                            except json.JSONDecodeError:
                                pass
                    
                    # 流式完成后，先创建新消息，再删除旧消息
                    if new_content:
                        # 创建新的AI消息
                        new_ai_message = models.Message(
                            thread_id=thread_id,
                            role="assistant",
                            content=new_content,
                            parent_id=user_message_id,
                            model_used=model_to_use,
                            created_at=datetime.utcnow()
                        )
                        db.add(new_ai_message)
                        db.commit()
                        db.refresh(new_ai_message)
                        
                        # 只删除AI消息，保留用户消息
                        success, message, delete_info = manager.delete_ai_message_only(message_id, current_user["id"])
                        if not success:
                          logger.error(f"删除旧AI消息失败: {message}")
                          # 继续执行，因为我们需要创建新消息

                        # 更新线程状态
                        thread = db.query(models.Thread).filter(
                            models.Thread.id == thread_id
                        ).first()
                        if thread:
                            thread.is_active = True
                            thread.updated_at = datetime.utcnow()
                            db.commit()
                        
                        # 发送包含新消息ID的完成消息
                        message_data = json.dumps({
                            "content": "",
                            "done": True,
                            "message_id": new_ai_message.id,
                            "user_message_id": user_message_id,
                            "model_used": model_to_use
                        })
                        yield f"data: {message_data}\n\n"
                    else:
                        # 没有生成内容，返回错误
                        error_data = json.dumps({
                            "content": "重新生成失败：未生成任何内容",
                            "error": True,
                            "done": True
                        })
                        yield f"data: {error_data}\n\n"
                        
                except Exception as e:
                    logger.error(f"流式重新生成失败: {str(e)}")
                    error_data = json.dumps({
                        "content": f"重新生成失败: {str(e)}",
                        "error": True,
                        "done": True
                    })
                    yield f"data: {error_data}\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
            
        else:
            # 非流式响应
            # 先调用AI服务
            ai_response = await ai_service.chat_completion(
                messages=ai_messages,
                model=model_to_use,
                stream=False,
                user_id=current_user["username"]
            )
            
            # 创建新的AI消息
            new_ai_message = models.Message(
                thread_id=thread_id,
                role="assistant",
                content=ai_response["content"],
                parent_id=user_message.id,
                model_used=ai_response.get("model_used"),
                tokens=ai_response.get("tokens"),
                created_at=datetime.utcnow()
            )
            db.add(new_ai_message)
            
            # 只删除AI消息，保留用户消息
            success, message, delete_info = manager.delete_ai_message_only(message_id, current_user["id"])
            if not success:
                logger.error(f"删除旧AI消息失败: {message}")
                # 继续执行，因为我们需要创建新消息

            # 更新线程状态
            thread = db.query(models.Thread).filter(
                models.Thread.id == thread_id
            ).first()
            if thread:
                thread.is_active = True
                thread.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(new_ai_message)
            
            return {
                "code": 200,
                "message": "消息重新生成成功",
                "data": {
                    "new_message": new_ai_message,
                    "old_message_id": message_id,
                    "user_message_id": user_message.id
                }
            }
            
    except ValueError as e:
        # 处理Token用量上限错误
        logger.warning(f"AI服务调用被限制: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"重新生成消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新生成消息失败: {str(e)}"
        )

@router.get("/chat/usage/")
async def get_ai_usage(
    current_user: dict = Depends(get_current_user)
):
    """获取当前AI用量信息"""
    try:
        usage_info = ai_service.get_usage_info()
        return {
            "code": 200,
            "message": "成功获取用量信息",
            "data": usage_info
        }
    except Exception as e:
        logger.error(f"获取用量信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用量信息失败: {str(e)}"
        )


@router.get("/chat/models/")
async def get_available_models(
    current_user: dict = Depends(get_current_user)
):
    """获取可用的AI模型列表"""
    try:
        models_list = ai_service.get_available_models()
        return {
            "code": 200,
            "message": "成功获取模型列表",
            "data": {
                "models": models_list,
                "default_model": ai_service.get_default_model()
            }
        }
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型列表失败: {str(e)}"
        )


# ==================== 分支创建端点 ====================

@router.post("/branch/")
async def create_branch(
    request: schemas.CreateBranchRequest,
    current_user: dict = Depends(get_current_user),  # 添加认证
    db: Session = Depends(get_db)
):
    """创建新的对话分支（仅限最新消息 + 深度限制）"""
    try:
        # 1. 验证对话存在和所有权
        conversation = db.query(models.Conversation)\
            .filter(models.Conversation.id == request.conversation_id)\
            .first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        if conversation.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="无权在此对话中创建分支")
        
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
        
        # 5. 获取当前对话的线程数（用于生成标题）
        thread_count = db.query(models.Thread)\
            .filter(models.Thread.conversation_id == request.conversation_id)\
            .count()
        
        # 6. 生成智能分支标题
        # 首先尝试获取用户的问题
        user_question_content = None
        if parent_message.parent_id:
            # 查找父消息的父消息（用户提问）
            user_question = db.query(models.Message)\
              .filter(models.Message.id == parent_message.parent_id)\
              .first()
            if user_question and user_question.role == "user":
                user_question_content = user_question.content

        # 优先使用用户问题生成标题，如果没有则使用AI回复
        title_source = user_question_content if user_question_content else parent_message.content

        thread_title = ai_service.generate_branch_title(
            parent_message_content=title_source,  # 使用用户问题或AI回复
            thread_count=thread_count + 1,
            depth=parent_thread.depth + 1
        )
        
        # 7. 创建新线程（关键：设置 depth = 父线程 depth + 1）
        new_thread = models.Thread(
            conversation_id=request.conversation_id,
            parent_message_id=request.parent_message_id,
            title=thread_title,  # 使用智能生成的标题
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            depth=parent_thread.depth + 1  # ===== 核心：继承父深度+1 =====
        )
        db.add(new_thread)
        db.commit()
        db.refresh(new_thread)
        
        # 8. 复制历史消息到新线程
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
        
        # 9. 如果有新消息，添加到新线程
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
        
        # 10. 将新线程设为活跃，其他线程设为非活跃
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