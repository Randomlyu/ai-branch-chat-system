import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        """初始化AI服务，支持多种模型"""
        self.model_providers = {}
        self._setup_providers()
        
    def _setup_providers(self):
        """配置可用的AI模型提供商"""
        # DeepSeek配置
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_api_key:
            self.model_providers["deepseek-chat"] = {
                "client": OpenAI(
                    api_key=deepseek_api_key,
                    base_url="https://api.deepseek.com"
                ),
                "model": "deepseek-chat"
            }
        
        # OpenAI配置
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.model_providers["gpt-4"] = {
                "client": OpenAI(api_key=openai_api_key),
                "model": "gpt-4"
            }
            self.model_providers["gpt-3.5-turbo"] = {
                "client": OpenAI(api_key=openai_api_key),
                "model": "gpt-3.5-turbo"
            }
        
        # 如果没有配置任何API密钥，使用模拟模式
        if not self.model_providers:
            logger.warning("没有配置任何AI API密钥，将使用模拟模式")
            self.model_providers["mock"] = {"client": None, "model": "mock"}
    
    def get_available_models(self) -> list:
        """获取可用的模型列表"""
        return list(self.model_providers.keys())
    
    def chat_completion(
        self, 
        messages: list, 
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        调用AI模型进行对话补全
        
        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            Dict包含content, model_used, tokens等信息
        """
        try:
            # 检查模型是否可用
            if model not in self.model_providers:
                available_models = self.get_available_models()
                if "mock" in available_models:
                    model = "mock"
                else:
                    raise ValueError(f"模型 '{model}' 不可用。可用模型: {available_models}")
            
            provider = self.model_providers[model]
            
            # 模拟模式（用于测试）
            if model == "mock":
                return self._mock_chat_completion(messages)
            
            # 真实API调用
            client = provider["client"]
            model_name = provider["model"]
            
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # 提取响应
            ai_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            
            return {
                "content": ai_response,
                "model_used": model_name,
                "tokens": tokens_used
            }
            
        except Exception as e:
            logger.error(f"AI服务调用失败: {str(e)}")
            raise
    
    def _mock_chat_completion(self, messages: list) -> Dict[str, Any]:
        """模拟AI响应（用于测试）"""
        last_message = messages[-1]["content"] if messages else "你好"
        
        # 简单的模拟回复
        responses = {
            "hello": "你好！我是AI助手，很高兴为你服务！",
            "python": "Python是一种高级编程语言，以简洁易读的语法而闻名。",
            "java": "Java是一种面向对象的编程语言，具有'一次编写，到处运行'的特点。",
            "default": f"我收到了你的消息：'{last_message}'。这是一个模拟回复，请配置真实的AI API密钥。"
        }
        
        content = responses.get(last_message.lower(), responses["default"])
        
        return {
            "content": content,
            "model_used": "mock",
            "tokens": len(content) // 4  # 粗略估算
        }
    
    def count_tokens(self, text: str, model: str = "deepseek-chat") -> int:
        """
        估算文本的token数量
        
        Note: 这是一个简化的估算，实际应该使用对应模型的tokenizer
        """
        # 简化的估算：中文大约1个token=1-2个字，英文大约1个token=0.75个单词
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        # 粗略估算
        estimated_tokens = chinese_chars + int(other_chars * 0.3)
        
        return estimated_tokens


# 创建全局AI服务实例
ai_service = AIService()