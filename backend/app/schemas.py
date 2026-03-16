from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ThreadUpdate(BaseModel):
    title: str

# 基础模型
class MessageBase(BaseModel):
    thread_id: int
    role: str
    content: str
    parent_id: Optional[int] = None
    model_used: Optional[str] = None
    tokens: Optional[int] = None


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ThreadBase(BaseModel):
    conversation_id: int
    parent_message_id: Optional[int] = None
    title: Optional[str] = None
    is_active: bool = False
    # ===== 新增字段（插入在 is_active 之后）=====
    depth: int = 0  # 分支深度：主分支=0，每分支+1
    # ============================================

class ThreadCreate(ThreadBase):
    pass


class Thread(ThreadBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: Optional[str] = None


class Conversation(ConversationBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# API请求/响应模型
class SendMessageRequest(BaseModel):
    thread_id: int
    content: str
    parent_id: Optional[int] = None
    model: Optional[str] = None


class SendMessageResponse(BaseModel):
    user_message: Message
    ai_message: Message
    conversation_id: int
    thread_id: int


class CreateBranchRequest(BaseModel):
    conversation_id: int
    parent_message_id: int
    new_message_content: Optional[str] = None

class DeleteMessageRequest(BaseModel):
    """删除消息请求模型"""
    pass


class DeleteMessageResponse(BaseModel):
    """删除消息响应模型"""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class MessageDeleteInfo(BaseModel):
    """消息删除详情"""
    deleted_messages: List[int]
    fixed_messages: List[int]
    connection_point: Optional[int] = None
    is_latest_deleted: bool

class RegenerateMessageRequest(BaseModel):
    """重新生成消息请求模型"""
    model: Optional[str] = None
    stream: bool = False


class RegenerateMessageResponse(BaseModel):
    """重新生成消息响应模型"""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class RegenerateMessageData(BaseModel):
    """重新生成消息数据模型"""
    new_message: Message
    old_message_id: int
    user_message_id: int