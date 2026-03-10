from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime


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