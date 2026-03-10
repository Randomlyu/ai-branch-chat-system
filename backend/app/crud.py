from sqlalchemy.orm import Session
from app import models, schemas
from typing import Optional
from typing import List, Dict, Any

# 对话CRUD
def create_conversation(db: Session, conversation: schemas.ConversationCreate):
    db_conversation = models.Conversation(title=conversation.title)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    
    # 创建初始线程
    initial_thread = models.Thread(
        conversation_id=db_conversation.id,
        title="主分支"
    )
    db.add(initial_thread)
    db.commit()
    db.refresh(initial_thread)
    
    return db_conversation

def get_conversation(db: Session, conversation_id: int):
    return db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

def get_conversations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Conversation).offset(skip).limit(limit).all()

# 线程CRUD
def create_thread(db: Session, thread: schemas.ThreadCreate):
    db_thread = models.Thread(
        conversation_id=thread.conversation_id,
        parent_message_id=thread.parent_message_id,
        title=thread.title
    )
    db.add(db_thread)
    db.commit()
    db.refresh(db_thread)
    return db_thread

def get_thread(db: Session, thread_id: int):
    return db.query(models.Thread).filter(
        models.Thread.id == thread_id
    ).first()

# 消息CRUD
def create_message(db: Session, message: schemas.MessageCreate):
    db_message = models.Message(
        thread_id=message.thread_id,
        role=message.role,
        content=message.content,
        model_used=message.model_used
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_thread_messages(db: Session, thread_id: int, limit: int = 50):
    return db.query(models.Message).filter(
        models.Message.thread_id == thread_id
    ).order_by(models.Message.created_at).limit(limit).all()

def get_message_history(db: Session, message_id: int) -> List[models.Message]:
    """
    获取从对话开始到指定消息的所有历史消息
    
    算法：
    1. 找到该消息所在的线程
    2. 获取该线程中的所有消息
    3. 按时间排序
    4. 返回直到（包括）指定消息的所有消息
    """
    # 获取消息
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        return []
    
    # 获取线程中的所有消息
    thread_messages = db.query(models.Message)\
        .filter(models.Message.thread_id == message.thread_id)\
        .order_by(models.Message.created_at.asc())\
        .all()
    
    # 找到指定消息的位置
    result = []
    for msg in thread_messages:
        result.append(msg)
        if msg.id == message_id:
            break
    
    return result


def deactivate_other_threads(db: Session, conversation_id: int, active_thread_id: int) -> None:
    """
    停用同一对话中的其他线程，确保只有一个活跃线程
    """
    db.query(models.Thread)\
        .filter(
            models.Thread.conversation_id == conversation_id,
            models.Thread.id != active_thread_id,
            models.Thread.is_active == True
        )\
        .update({"is_active": False})
    db.commit()


def get_thread_tree(db: Session, conversation_id: int) -> List[Dict]:
    """
    获取对话的分支树
    
    返回线程的树形结构，用于前端可视化
    """
    # 获取对话的所有线程
    threads = db.query(models.Thread)\
        .filter(models.Thread.conversation_id == conversation_id)\
        .order_by(models.Thread.created_at.asc())\
        .all()
    
    # 构建线程映射
    thread_dict = {thread.id: thread for thread in threads}
    
    # 构建父子关系
    children = {}
    root_nodes = []
    
    for thread in threads:
        if thread.parent_message_id:
            # 找到父消息所在的线程
            parent_message = db.query(models.Message)\
                .filter(models.Message.id == thread.parent_message_id)\
                .first()
            if parent_message:
                parent_thread_id = parent_message.thread_id
                if parent_thread_id not in children:
                    children[parent_thread_id] = []
                children[parent_thread_id].append(thread)
                continue
        
        # 没有父消息的线程是根节点
        root_nodes.append(thread)
    
    # 递归构建树
    def build_tree(node):
        thread_data = {
            "id": node.id,
            "conversation_id": node.conversation_id,
            "parent_message_id": node.parent_message_id,
            "title": node.title,
            "is_active": node.is_active,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None,
            "children": []
        }
        
        if node.id in children:
            for child in children[node.id]:
                thread_data["children"].append(build_tree(child))
        
        return thread_data
    
    # 构建完整的树
    tree = []
    for root in root_nodes:
        tree.append(build_tree(root))
    
    return tree