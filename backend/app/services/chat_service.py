from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import openai
import os
from dotenv import load_dotenv

from app import crud, schemas, models
from app.database import get_db

load_dotenv()

class ChatService:
    def __init__(self):
        # 配置OpenAI API（暂时硬编码，后续从环境变量读取）
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        if self.api_key:
            openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
    
    async def process_message(
        self, 
        db: Session, 
        request: schemas.ChatRequest
    ) -> schemas.ChatResponse:
        """处理用户消息并调用AI API"""
        
        # 1. 保存用户消息
        user_message = crud.create_message(
            db=db,
            message=schemas.MessageCreate(
                thread_id=request.thread_id,
                role="user",
                content=request.message,
                model_used=request.model
            )
        )
        
        # 2. 获取对话历史
        history_messages = self._get_conversation_history(db, request.thread_id)
        
        # 3. 调用AI API
        ai_response = await self._call_ai_api(
            messages=history_messages + [{"role": "user", "content": request.message}],
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # 4. 保存AI回复
        ai_message = crud.create_message(
            db=db,
            message=schemas.MessageCreate(
                thread_id=request.thread_id,
                role="assistant",
                content=ai_response["content"],
                model_used=request.model
            )
        )
        
        return schemas.ChatResponse(
            message_id=ai_message.id,
            content=ai_response["content"],
            role="assistant",
            thread_id=request.thread_id,
            tokens_used=ai_response.get("tokens", 0),
            model_used=request.model
        )
    
    async def create_branch(
        self,
        db: Session,
        request: schemas.BranchCreateRequest
    ) -> schemas.Thread:
        """创建新分支"""
        # 获取父消息
        parent_message = db.query(models.Message).filter(
            models.Message.id == request.parent_message_id
        ).first()
        
        if not parent_message:
            raise ValueError("父消息不存在")
        
        # 创建新线程
        new_thread = crud.create_thread(
            db=db,
            thread=schemas.ThreadCreate(
                conversation_id=request.conversation_id,
                parent_message_id=request.parent_message_id,
                title=f"分支-{parent_message.content[:20]}..."
            )
        )
        
        # 如果需要，添加初始消息
        if request.new_message:
            crud.create_message(
                db=db,
                message=schemas.MessageCreate(
                    thread_id=new_thread.id,
                    role="user",
                    content=request.new_message
                )
            )
        
        return new_thread
    
    def _get_conversation_history(
        self, 
        db: Session, 
        thread_id: int,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """获取对话历史，格式化为OpenAI消息格式"""
        messages = crud.get_thread_messages(db, thread_id, limit)
        
        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return history
    
    async def _call_ai_api(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """调用AI API（这里以OpenAI为例）"""
        
        if not self.client:
            # 模拟API响应（用于测试）
            return {
                "content": f"[模拟响应] 这是对您消息的回复: {messages[-1]['content']}",
                "tokens": 50
            }
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "tokens": response.usage.total_tokens
            }
            
        except Exception as e:
            return {
                "content": f"调用AI API时出错: {str(e)}",
                "tokens": 0
            }