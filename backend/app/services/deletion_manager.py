"""
删除管理器 - 应用层控制删除逻辑
支持批量删除、错误处理、未来扩展
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Tuple, List, Optional
import logging
from datetime import datetime, timedelta
from .. import models

logger = logging.getLogger(__name__)


class DeletionManager:
    def __init__(self, db: Session):
        self.db = db
        
    def delete_conversation(self, conversation_id: int, user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        删除对话及其所有关联数据
        
        返回: (是否成功, 消息)
        """
        try:
            # 1. 查找对话
            query = self.db.query(models.Conversation).filter(
                models.Conversation.id == conversation_id
            )
            
            if user_id is not None:
                query = query.filter(models.Conversation.user_id == user_id)
                
            conversation = query.first()
            
            if not conversation:
                return False, "对话不存在或无权访问"
            
            conversation_title = conversation.title
            
            # 2. 查找对话的所有线程
            threads = self.db.query(models.Thread).filter(
                models.Thread.conversation_id == conversation_id
            ).all()
            
            thread_ids = [thread.id for thread in threads]
            
            # 3. 批量删除消息
            if thread_ids:
                # 删除消息
                self.db.query(models.Message).filter(
                    models.Message.thread_id.in_(thread_ids)
                ).delete(synchronize_session=False)
                
                # 删除线程
                self.db.query(models.Thread).filter(
                    models.Thread.conversation_id == conversation_id
                ).delete(synchronize_session=False)
            
            # 4. 删除对话
            self.db.delete(conversation)
            self.db.commit()
            
            logger.info(f"对话删除成功: {conversation_title} (ID: {conversation_id})")
            return True, f"对话 '{conversation_title}' 已删除"
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"数据库错误 - 删除对话 {conversation_id}: {str(e)}")
            return False, f"数据库错误: {str(e)}"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"未知错误 - 删除对话 {conversation_id}: {str(e)}")
            return False, f"未知错误: {str(e)}"
    
    def get_conversation_stats(self, conversation_id: int) -> dict:
        """
        获取对话统计信息（用于确认删除前的显示）
        """
        conversation = self.db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return {}
        
        # 统计线程数
        thread_count = self.db.query(models.Thread).filter(
            models.Thread.conversation_id == conversation_id
        ).count()
        
        # 统计消息总数
        if thread_count > 0:
            thread_ids = [t.id for t in self.db.query(models.Thread.id).filter(
                models.Thread.conversation_id == conversation_id
            ).all()]
            
            message_count = self.db.query(models.Message).filter(
                models.Message.thread_id.in_(thread_ids)
            ).count()
        else:
            message_count = 0
        
        return {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            "thread_count": thread_count,
            "message_count": message_count
        }