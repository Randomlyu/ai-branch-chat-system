from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from datetime import datetime, timezone, timedelta
import pytz

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def to_beijing_time(dt: Union[datetime, str, None]) -> Optional[datetime]:
    """将时间转换为北京时间"""
    if dt is None:
        return None
    
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    # 如果datetime是naive（没有时区信息），假定为UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # 转换为北京时间
    return dt.astimezone(BEIJING_TZ)

def format_datetime_for_display(dt: datetime) -> str:
    """格式化时间为字符串，用于前端显示"""
    beijing_dt = to_beijing_time(dt)
    return beijing_dt.isoformat()

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
    @field_serializer('created_at')
    def serialize_created_at(self, created_at: datetime, _info) -> str:
        """将created_at字段序列化为北京时间字符串"""
        beijing_time = to_beijing_time(created_at)
        return beijing_time.isoformat()
    model_config = ConfigDict(from_attributes=True)


class ThreadBase(BaseModel):
    conversation_id: int
    parent_message_id: Optional[int] = None
    title: Optional[str] = None
    is_active: bool = False
    depth: int = Field(default=0, description="分支深度：主分支=0，每分支+1，最大3")
    
    # ===== 新增字段 =====
    parent_thread_id: Optional[int] = Field(
        default=None, 
        description="父线程ID，用于快速判断是否有子线程，主线程为None"
    )
    # ==================


class ThreadCreate(ThreadBase):
    pass


class Thread(ThreadBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    # 可选的子线程列表（用于API响应，便于前端构建树）
    child_threads: Optional[List["Thread"]] = None
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime_fields(self, dt: datetime, _info) -> str:
        """将时间字段序列化为北京时间字符串"""
        beijing_time = to_beijing_time(dt)
        return beijing_time.isoformat()
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
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime_fields(self, dt: datetime, _info) -> str:
        """将时间字段序列化为北京时间字符串"""
        beijing_time = to_beijing_time(dt)
        return beijing_time.isoformat()
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


# ===== 新增：删除线程请求/响应模型 =====
class DeleteThreadRequest(BaseModel):
    """删除线程请求模型"""
    pass


class DeleteThreadResponse(BaseModel):
    """删除线程响应模型"""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class ThreadDeleteInfo(BaseModel):
    """线程删除详情"""
    deleted_thread_id: int
    deleted_message_ids: List[int]
    parent_thread_id: Optional[int] = None
    # ============================================


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

# ===== 新增：消息编辑相关模型 =====
class CheckMessageEditableRequest(BaseModel):
    """检查消息是否可编辑的请求模型"""
    message_id: int


class CheckMessageEditableResponse(BaseModel):
    """检查消息是否可编辑的响应模型"""
    is_editable: bool
    reason: Optional[str] = None


class UpdateUserMessageRequest(BaseModel):
    """更新用户消息的请求模型"""
    content: str
    model: Optional[str] = None


class UpdateUserMessageResponse(BaseModel):
    """更新用户消息的响应模型"""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class UpdateUserMessageData(BaseModel):
    """更新用户消息数据模型"""
    updated_user_message: Message
    new_ai_message: Message
    conversation_id: int
    thread_id: int
# ===================================