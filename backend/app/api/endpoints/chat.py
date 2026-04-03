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
from ...models import User  # 添加User模型导入

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
    current_user: User = Depends(get_current_user),  # 修改为User类型
    db: Session = Depends(get_db)
):
    """创建新对话"""
    try:
        # 使用认证用户ID
        db_conversation = models.Conversation(
            title=conversation.title,
            user_id=current_user.id,  # 修改为属性访问
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
    current_user: User = Depends(get_current_user),  # 修改为User类型
    db: Session = Depends(get_db)
):
    """获取当前用户的对话列表（按更新时间倒序）"""
    try:
        conversations = (
           db.query(models.Conversation)
           .filter(models.Conversation.user_id == current_user.id)  # 修改为属性访问
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
    current_user: User = Depends(get_current_user),  # 修改为User类型
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
    if db_conversation.user_id != current_user.id:  # 修改为属性访问
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此对话"
        )
    
    return db_conversation


@router.put("/conversations/{conversation_id}", response_model=schemas.Conversation)
def update_conversation(
    conversation_id: int,
    conversation: schemas.ConversationUpdate,
    current_user: User = Depends(get_current_user),  # 修改为User类型
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
    if db_conversation.user_id != current_user.id:  # 修改为属性访问
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
    current_user: User = Depends(get_current_user),  # 修改为User类型
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
        
        if conversation.user_id != current_user.id:  # 修改为属性访问
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此对话"
            )
        
        # 创建删除管理器
        manager = DeletionManager(db)
        
        # 执行删除
        success, message = manager.delete_conversation(conversation_id, current_user.id)  # 修改为属性访问
        
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
    current_user: User = Depends(get_current_user),  # 修改为User类型
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
    
    if conversation.user_id != current_user.id:  # 修改为属性访问
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
    current_user: User = Depends(get_current_user),  # 修改为User类型
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
    
    if conversation.user_id != current_user.id:  # 修改为属性访问
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
    current_user: User = Depends(get_current_user),  # 修改为User类型
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
    
    if conversation and conversation.user_id != current_user.id:  # 修改为属性访问
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此线程"
        )
    
    return thread

@router.put("/threads/{thread_id}", response_model=schemas.Thread)
def update_thread_title(
    thread_id: int,
    thread_update: schemas.ThreadUpdate,  # 需要创建这个Pydantic模型
    current_user: User = Depends(get_current_user),  # 修改为User类型
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
    
    if conversation.user_id != current_user.id:  # 修改为属性访问
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

@router.delete("/threads/{thread_id}", response_model=schemas.DeleteThreadResponse)
def delete_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),  # 修改为User类型
    db: Session = Depends(get_db)
):
    """
    删除叶子线程
    规则：1. 必须是叶子节点（没有子线程） 2. 不能是主线程（depth != 0）
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
        
        if conversation.user_id != current_user.id:  # 修改为属性访问
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此线程"
            )
        
        # 3. 检查是否是主线程（depth=0不允许删除）
        if thread.depth == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="主线程不允许删除"
            )
        
        # 4. 检查是否是叶子节点（是否有子线程）
        has_children = db.query(models.Thread).filter(
            models.Thread.parent_thread_id == thread_id
        ).first()
        
        if has_children:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此线程包含子线程，无法删除。请先删除所有子线程。"
            )
        
        # 5. 获取线程的所有消息ID（用于返回给前端）
        message_ids = [
            msg.id for msg in 
            db.query(models.Message.id)
            .filter(models.Message.thread_id == thread_id)
            .all()
        ]
        
        # 6. 删除线程的所有消息
        db.query(models.Message).filter(
            models.Message.thread_id == thread_id
        ).delete(synchronize_session=False)
        
        # 7. 如果删除的是活跃线程，需要设置新的活跃线程
        if thread.is_active:
            # 查找同一对话中的其他线程
            other_thread = db.query(models.Thread).filter(
                models.Thread.conversation_id == thread.conversation_id,
                models.Thread.id != thread_id
            ).order_by(models.Thread.created_at.asc()).first()
            
            if other_thread:
                other_thread.is_active = True
                other_thread.updated_at = datetime.utcnow()
            else:
                # 如果没有其他线程，将对话标记为无活跃线程
                # 这应该不会发生，因为主线程还在
                pass
        
        # 8. 删除线程
        db.delete(thread)
        db.commit()
        
        # 9. 返回成功响应
        return {
            "code": 200,
            "message": "线程删除成功",
            "data": {
                "deleted_thread_id": thread_id,
                "deleted_message_ids": message_ids,
                "parent_thread_id": thread.parent_thread_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除线程失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除线程失败: {str(e)}"
        )

@router.get("/threads/{thread_id}/messages", response_model=List[schemas.Message])
def get_thread_messages(
    thread_id: int,
    current_user: User = Depends(get_current_user),  # 修改为User类型
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
    
    if conversation and conversation.user_id != current_user.id:  # 修改为属性访问
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

@router.post("/chat/stream/")
async def send_message_stream(
    request: schemas.SendMessageRequest,
    current_user: User = Depends(get_current_user),  # 修改为User类型
    db: Session = Depends(get_db)
):
    """
    发送消息并获取AI回复（流式版本）
    这是唯一支持的消息发送端点
    """
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
            
            if conversation and conversation.user_id != current_user.id:  # 修改为属性访问
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
            is_interrupted = False  # 新增：标记是否被中断

            # 生成流式响应
            stream_generator = ai_service.stream_chat_completion(
                messages=ai_messages,
                model=model,
                user_id=current_user.username  # 修改为属性访问
            )
            
            try:
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
            except Exception as e:
                # 捕获中断异常
                logger.info(f"流式生成被中断: {str(e)}")
                is_interrupted = True
                # 不重新抛出异常，继续处理
            
            # 6. 创建AI回复消息
            if is_interrupted:
               # 只要被中断，就保存为"您中断了生成"
               ai_response_content = "您中断了生成"
               logger.info(f"流式生成被中断，将保存中断消息: {ai_response_content}")
            
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
                "model_used": model or ai_service.get_default_model(),
                "is_interrupted": is_interrupted  # 新增：标记是否是中断消息
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
    current_user: User = Depends(get_current_user)  # 修改为User类型
):
    """停止当前用户的流式生成"""
    try:
        ai_service.stop_user_request(current_user.username)  # 修改为属性访问
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
    current_user: User = Depends(get_current_user),  # 修改为User类型
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
        
        if conversation.user_id != current_user.id:  # 修改为属性访问
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
            current_user.id  # 修改为属性访问
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

@router.post("/threads/{thread_id}/messages/{message_id}/regenerate")
async def regenerate_message_stream(
    thread_id: int,
    message_id: int,
    request: schemas.RegenerateMessageRequest,
    current_user: User = Depends(get_current_user),  # 修改为User类型
    db: Session = Depends(get_db)
):
    """
    重新生成AI消息（流式版本）
    规则：1. 必须是AI消息 2. 必须是最新消息 3. 不能被分支引用
    """
    async def stream_generator():
        new_ai_message = None
        new_content = ""
        
        try:
            # 1. 创建删除管理器
            manager = DeletionManager(db)
            
            # 2. 验证是否可以重新生成
            can_regenerate, message_text, regenerate_info = manager.regenerate_message(
                ai_message_id=message_id,
                model=request.model,
                stream=True,  # 总是使用流式
                user_id=current_user.id  # 修改为属性访问
            )
            
            if not can_regenerate:
                error_data = json.dumps({
                    "content": message_text,
                    "error": True,
                    "done": True
                })
                yield f"data: {error_data}\n\n"
                return
            
            # 3. 获取原消息信息
            old_ai_message = db.query(models.Message).filter(
                models.Message.id == message_id
            ).first()
            
            if not old_ai_message:
                error_data = json.dumps({
                    "content": "原消息不存在",
                    "error": True,
                    "done": True
                })
                yield f"data: {error_data}\n\n"
                return
            
            # 4. 获取对应的用户消息
            user_message = db.query(models.Message).filter(
                models.Message.id == old_ai_message.parent_id
            ).first()
            
            if not user_message:
                error_data = json.dumps({
                    "content": "用户消息不存在",
                    "error": True,
                    "done": True
                })
                yield f"data: {error_data}\n\n"
                return
            
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
            
            # 6. 调用AI流式服务
            model_to_use = request.model or old_ai_message.model_used
            
            # 注意：不要在生成器开始时立即删除旧消息
            # 先获取所有必要信息
            old_message_id = old_ai_message.id
            old_message_content = old_ai_message.content
            user_message_id = user_message.id
            
            # 调用AI流式服务
            ai_stream_generator = ai_service.stream_chat_completion(
                messages=ai_messages,
                model=model_to_use,
                user_id=current_user.username  # 修改为属性访问
            )
            
            # 流式生成内容
            async for chunk in ai_stream_generator:
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
                success, message, delete_info = manager.delete_ai_message_only(message_id, current_user.id)  # 修改为属性访问
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
                
        except ValueError as e:
            # 处理Token用量上限错误
            logger.warning(f"AI服务调用被限制: {str(e)}")
            error_data = json.dumps({
                "content": str(e),
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

@router.get("/chat/usage/")
async def get_ai_usage(
    current_user: User = Depends(get_current_user)  # 修改为User类型
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
    current_user: User = Depends(get_current_user)  # 修改为User类型
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
    current_user: User = Depends(get_current_user),  # 修改为User类型
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
        
        if conversation.user_id != current_user.id:  # 修改为属性访问
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
        # 使用AI回复（parent_message）的内容生成标题
        # parent_message是AI消息，包含了AI的回复内容
        thread_title = ai_service.generate_branch_title(
            parent_message_content=parent_message.content,  # 使用AI回复内容
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
            depth=parent_thread.depth + 1,  # ===== 核心：继承父深度+1 =====
            # ===== 新增：设置父线程ID =====
            parent_thread_id=parent_thread.id
            # ============================
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

# ===== 新增：消息编辑相关端点 =====
@router.get("/messages/{message_id}/editable")
def check_message_editable(
    message_id: int,
    current_user: User = Depends(get_current_user),  # 修改为User类型
    db: Session = Depends(get_db)
):
    """
    检查消息是否可编辑
    规则：1. 必须是用户消息 2. 必须是最新用户消息 3. 不能被分支引用
    """
    try:
        # 1. 验证消息存在
        message = db.query(models.Message).filter(
            models.Message.id == message_id
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="消息不存在"
            )
        
        # 2. 验证消息所有权
        # 通过线程和对话验证所有权
        thread = db.query(models.Thread).filter(
            models.Thread.id == message.thread_id
        ).first()
        
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="线程不存在"
            )
        
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == thread.conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
        
        if conversation.user_id != current_user.id:  # 修改为属性访问
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权编辑此消息"
            )
        
        # 3. 验证是否是用户消息
        if message.role != "user":
            return {
                "code": 200,
                "message": "检查完成",
                "data": {
                    "is_editable": False,
                    "reason": "只能编辑用户消息"
                }
            }
        
        # 4. 检查是否被分支引用
        # 查找是否有线程以此消息为父消息
        branch_thread = db.query(models.Thread).filter(
            models.Thread.parent_message_id == message_id
        ).first()
        
        if branch_thread:
            return {
                "code": 200,
                "message": "检查完成",
                "data": {
                    "is_editable": False,
                    "reason": "此消息已被分支引用，无法编辑"
                }
            }
        
        # 5. 检查是否是最新用户消息
        # 获取该线程的所有用户消息
        user_messages = db.query(models.Message).filter(
            models.Message.thread_id == message.thread_id,
            models.Message.role == "user"
        ).order_by(models.Message.created_at.desc()).all()
        
        if not user_messages or user_messages[0].id != message_id:
            return {
                "code": 200,
                "message": "检查完成",
                "data": {
                    "is_editable": False,
                    "reason": "只能编辑最新的用户消息"
                }
            }
        
        # 6. 检查此用户消息是否有AI回复
        ai_reply = db.query(models.Message).filter(
            models.Message.thread_id == message.thread_id,
            models.Message.role == "assistant",
            models.Message.parent_id == message_id
        ).first()
        
        # 如果AI回复已被分支引用，则不能编辑
        if ai_reply:
            ai_reply_branch = db.query(models.Thread).filter(
                models.Thread.parent_message_id == ai_reply.id
            ).first()
            
            if ai_reply_branch:
                return {
                    "code": 200,
                    "message": "检查完成",
                    "data": {
                        "is_editable": False,
                        "reason": "此消息对应的AI回复已被分支引用，无法编辑"
                    }
                }
        
        # 7. 所有检查通过，消息可编辑
        return {
            "code": 200,
            "message": "检查完成",
            "data": {
                "is_editable": True,
                "reason": "消息可编辑"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查消息可编辑性失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查消息可编辑性失败: {str(e)}"
        )


@router.post("/messages/{message_id}/update")
async def update_user_message_stream(
    message_id: int,
    request: schemas.UpdateUserMessageRequest,
    current_user: User = Depends(get_current_user),  # 修改为User类型
    db: Session = Depends(get_db)
):
    """
    更新用户消息（流式版本）
    流程：1. 验证消息可编辑 2. 更新用户消息 3. 删除原有AI回复 4. 重新生成AI回复
    """
    async def event_generator():
        try:
            # 1. 验证消息存在
            user_message = db.query(models.Message).filter(
                models.Message.id == message_id
            ).first()
            
            if not user_message:
                error_data = json.dumps({
                    "content": "消息不存在",
                    "error": True,
                    "done": True
                })
                yield f"data: {error_data}\n\n"
                return
            
            # 2. 验证消息所有权
            thread = db.query(models.Thread).filter(
                models.Thread.id == user_message.thread_id
            ).first()
            
            if not thread:
                error_data = json.dumps({
                    "content": "线程不存在",
                    "error": True,
                    "done": True
                })
                yield f"data: {error_data}\n\n"
                return
            
            conversation = db.query(models.Conversation).filter(
                models.Conversation.id == thread.conversation_id
            ).first()
            
            if not conversation:
                error_data = json.dumps({
                    "content": "对话不存在",
                    "error": True,
                    "done": True
                })
                yield f"data: {error_data}\n\n"
                return
            
            if conversation.user_id != current_user.id:  # 修改为属性访问
                error_data = json.dumps({
                    "content": "无权编辑此消息",
                    "error": True,
                    "done": True
                })
                yield f"data: {error_data}\n\n"
                return
            
            # 3. 验证消息可编辑性（复用检查逻辑）
            response = check_message_editable(message_id, current_user, db)  # 注意：这里current_user已经是User对象
            response_data = response["data"]
            
            if not response_data["is_editable"]:
                error_data = json.dumps({
                    "content": response_data["reason"] or "消息不可编辑",
                    "error": True,
                    "done": True
                })
                yield f"data: {error_data}\n\n"
                return
            
            # 4. 更新用户消息内容
            old_content = user_message.content
            user_message.content = request.content
            user_message.created_at = datetime.utcnow()  # 更新时间戳
            db.commit()
            
            # 5. 查找并删除原有的AI回复（如果有的话）
            old_ai_message = None
            ai_reply = db.query(models.Message).filter(
                models.Message.thread_id == user_message.thread_id,
                models.Message.role == "assistant",
                models.Message.parent_id == message_id
            ).first()
            
            if ai_reply:
                old_ai_message = ai_reply
                # 删除AI回复
                db.delete(ai_reply)
                db.commit()
            
            # 6. 获取历史消息（到被编辑的用户消息为止）
            history_messages = db.query(models.Message).filter(
                models.Message.thread_id == user_message.thread_id,
                models.Message.created_at <= user_message.created_at
            ).order_by(models.Message.created_at.asc()).all()
            
            # 构建AI消息格式
            ai_messages = []
            for msg in history_messages:
                if msg.id == message_id:
                    # 使用更新后的内容
                    ai_messages.append({"role": "user", "content": request.content})
                elif msg.role == "user":
                    ai_messages.append({"role": "user", "content": msg.content})
                else:
                    ai_messages.append({"role": "assistant", "content": msg.content})
            
            # 7. 调用AI流式服务重新生成回复
            model = request.model
            ai_response_content = ""
            is_interrupted = False
            
            stream_generator = ai_service.stream_chat_completion(
                messages=ai_messages,
                model=model,
                user_id=current_user.username  # 修改为属性访问
            )
            
            try:
                async for chunk in stream_generator:
                    yield chunk
                    
                    # 解析chunk以获取内容
                    if chunk.startswith("data: "):
                        try:
                            data_str = chunk[6:]
                            if data_str.strip():
                                data = json.loads(data_str.strip())
                                if "content" in data and not data.get("done") and not data.get("error"):
                                    ai_response_content += data["content"]
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                logger.info(f"流式生成被中断: {str(e)}")
                is_interrupted = True
            
            # 8. 创建新的AI回复消息
            if is_interrupted:
                ai_response_content = "您中断了生成"
            
            new_ai_message = models.Message(
                thread_id=user_message.thread_id,
                role="assistant",
                content=ai_response_content,
                parent_id=user_message.id,
                model_used=model or ai_service.get_default_model(),
                created_at=datetime.utcnow()
            )
            db.add(new_ai_message)
            db.flush()  # 刷新以获取消息ID
            
            # 9. 更新线程状态
            thread.is_active = True
            thread.updated_at = datetime.utcnow()
            db.commit()
            
            # 10. 发送完成消息
            message_data = json.dumps({
                "content": "",
                "done": True,
                "message_id": new_ai_message.id,
                "user_message_id": user_message.id,
                "model_used": model or ai_service.get_default_model(),
                "is_interrupted": is_interrupted
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
            logger.error(f"更新用户消息失败: {str(e)}")
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
            "X-Accel-Buffering": "no"
        }
    )
# ===========================================