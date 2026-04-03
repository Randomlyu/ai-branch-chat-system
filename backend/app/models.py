"""
优化的数据模型设计，解决多外键路径问题，支持未来扩展
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from .database import Base


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), default="新对话", index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, default=1, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), index=True)
    
    # 不设置级联删除，由应用层控制
    threads = relationship("Thread", back_populates="conversation")
    
    # 添加验证
    @validates('title')
    def validate_title(self, key, title):
        if not title or len(title.strip()) == 0:
            raise ValueError("对话标题不能为空")
        if len(title) > 200:
            raise ValueError("对话标题不能超过200字符")
        return title.strip()
    
    # 添加复合索引
    __table_args__ = (
        Index('idx_user_updated', 'user_id', 'updated_at'),
    )

class Thread(Base):
    __tablename__ = "threads"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    parent_message_id = Column(Integer, nullable=True)  # 不设置外键，减少约束
    title = Column(String(200), index=True)
    is_active = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), index=True)
    
    # ===== 新增字段（插入在 updated_at 之后）=====
    depth = Column(Integer, nullable=False, default=0, server_default="0", 
                  comment="分支深度：主分支=0，每分支+1，最大3")
    
    # 添加 parent_thread_id 字段
    parent_thread_id = Column(
        Integer, 
        ForeignKey("threads.id"),  # 自引用外键
        nullable=True,  # 主线程的 parent_thread_id 为 NULL
        index=True,
        comment="父线程ID，用于快速判断是否有子线程"
    )
    # ============================================

    # 明确指定外键，避免多路径问题
    conversation = relationship("Conversation", back_populates="threads")
    
    # 不设置级联，由应用层控制
    messages = relationship("Message", back_populates="thread")
    
    # 添加自引用关系
    parent_thread = relationship(
        "Thread", 
        remote_side=[id],  # 指定远程端是当前表的id字段
        backref="child_threads",  # 反向引用名称
        foreign_keys=[parent_thread_id]  # 明确指定外键
    )
    
    # 添加验证
    @validates('conversation_id')
    def validate_conversation_id(self, key, conversation_id):
        if conversation_id <= 0:
            raise ValueError("无效的对话ID")
        return conversation_id
    
    # 深度验证
    @validates('depth')
    def validate_depth(self, key, depth):
        if depth < 0 or depth > 3:
            raise ValueError("分支深度必须在0-3之间")
        return depth
    
    # 父线程验证
    @validates('parent_thread_id')
    def validate_parent_thread_id(self, key, parent_thread_id):
        if parent_thread_id is not None and parent_thread_id == self.id:
            raise ValueError("线程不能以自身为父线程")
        return parent_thread_id
    
    # 更新复合索引
    __table_args__ = (
        Index('idx_conversation_active', 'conversation_id', 'is_active'),
        Index('idx_conversation_parent', 'conversation_id', 'parent_message_id'),
        Index('idx_parent_thread', 'parent_thread_id'),  # 新增索引，优化查询
    )

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False, index=True)
    role = Column(String(20), index=True)  # 'user' or 'assistant'
    content = Column(Text)
    parent_id = Column(Integer, nullable=True)  # 不设置外键，减少约束
    model_used = Column(String(50), nullable=True, index=True)
    tokens = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 明确指定外键
    thread = relationship("Thread", back_populates="messages")
    
    # 添加验证
    @validates('thread_id')
    def validate_thread_id(self, key, thread_id):
        if thread_id <= 0:
            raise ValueError("无效的线程ID")
        return thread_id
    
    @validates('role')
    def validate_role(self, key, role):
        if role not in ['user', 'assistant']:
            raise ValueError("角色必须是user或assistant")
        return role
    
    # 复合索引
    __table_args__ = (
        Index('idx_thread_created', 'thread_id', 'created_at'),
        Index('idx_thread_parent', 'thread_id', 'parent_id'),
    )


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    need_password_change = Column(Boolean, default=True, index=True, server_default='1')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    # 添加与Conversation的关系
    conversations = relationship("Conversation", backref="user", cascade="all, delete-orphan")