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
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

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
    
    def delete_message_pair(self, ai_message_id: int, user_id: Optional[int] = None) -> Tuple[bool, str, Dict[str, Any]]:
   
     try:
        # 1. 验证AI消息存在
        ai_message = self.db.query(models.Message).filter(
            models.Message.id == ai_message_id
        ).first()
        
        if not ai_message:
            return False, "AI消息不存在", {}
        
        # 2. 验证必须是AI消息
        if ai_message.role != "assistant":
            return False, "只能删除AI消息", {}
        
        # 3. 验证线程存在
        thread = self.db.query(models.Thread).filter(
            models.Thread.id == ai_message.thread_id
        ).first()
        
        if not thread:
            return False, "线程不存在", {}
        
        # 4. 验证对话存在和所有权
        conversation = self.db.query(models.Conversation).filter(
            models.Conversation.id == thread.conversation_id
        ).first()
        
        if not conversation:
            return False, "对话不存在", {}
        
        if user_id is not None and conversation.user_id != user_id:
            return False, "无权删除此消息", {}
        
        # 5. 检查该消息是否被分支引用
        thread_refs = self.db.query(models.Thread).filter(
            models.Thread.parent_message_id == ai_message_id
        ).count()
        
        if thread_refs > 0:
            return False, "此消息已被分支引用，无法删除", {}
        
        # 6. 获取对应的用户消息
        user_message = self.db.query(models.Message).filter(
            models.Message.id == ai_message.parent_id,
            models.Message.role == "user"
        ).first()
        
        if not user_message:
            return False, "找不到对应的用户消息", {}
        
        # 7. 检查是否是最新消息
        latest_message = self.db.query(models.Message).filter(
            models.Message.thread_id == ai_message.thread_id
        ).order_by(models.Message.created_at.desc()).first()
        
        is_latest = latest_message and latest_message.id == ai_message_id
        
        # 8. 获取连接点ID（在删除前保存）
        connection_point_id = user_message.parent_id
        
        # 9. 获取需要修复的消息ID（在删除前保存）
        affected_message_ids = [
            msg.id for msg in self.db.query(models.Message.id).filter(
                models.Message.parent_id == ai_message_id
            ).all()
        ]
        
        # 10. 获取要删除的消息ID（在删除前保存）
        delete_message_ids = [user_message.id, ai_message.id]
        
        # 11. 先修复消息链：更新受影响消息的parent_id
        if affected_message_ids:
            self.db.query(models.Message).filter(
                models.Message.id.in_(affected_message_ids)
            ).update(
                {"parent_id": connection_point_id},
                synchronize_session=False
            )
        
        # 12. 删除消息
        self.db.query(models.Message).filter(
            models.Message.id.in_(delete_message_ids)
        ).delete(synchronize_session=False)
        
        # 13. 修复分支引用：更新引用被删消息的线程
        self.db.query(models.Thread).filter(
            models.Thread.parent_message_id.in_(delete_message_ids)
        ).update(
            {"parent_message_id": connection_point_id},
            synchronize_session=False
        )
        
        # 14. 如果删除的是最新消息，更新线程状态
        if is_latest:
            # 找到新的最新消息
            new_latest = self.db.query(models.Message).filter(
                models.Message.thread_id == thread.id
            ).order_by(models.Message.created_at.desc()).first()
            
            if new_latest:
                # 确保线程活跃状态正确
                thread.updated_at = datetime.utcnow()
            else:
                # 没有消息了，但线程仍然存在
                thread.is_active = False
                thread.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # 返回删除详情
        delete_info = {
            "deleted_messages": delete_message_ids,
            "fixed_messages": affected_message_ids,
            "connection_point": connection_point_id,
            "is_latest_deleted": is_latest
        }
        
        logger.info(f"消息删除成功: 删除{len(delete_message_ids)}条消息，修复{len(affected_message_ids)}条消息")
        return True, "消息删除成功", delete_info
        
     except SQLAlchemyError as e:
        self.db.rollback()
        logger.error(f"数据库错误 - 删除消息 {ai_message_id}: {str(e)}")
        return False, f"数据库错误: {str(e)}", {}
        
     except Exception as e:
        self.db.rollback()
        logger.error(f"未知错误 - 删除消息 {ai_message_id}: {str(e)}")
        return False, f"未知错误: {str(e)}", {}