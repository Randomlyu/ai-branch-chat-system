import os
import logging
import asyncio
import json
import threading
import re
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv
import pytz

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class TokenUsageTracker:
    """Token用量跟踪器，使用文件存储保证重启后数据不丢失"""
    
    def __init__(self, data_file: str = "token_usage.json"):
        self.data_file = Path(data_file)
        self._lock = threading.Lock()
        self._usage_data: Optional[Dict] = None
        self._beijing_tz = pytz.timezone('Asia/Shanghai')  # 北京时区
        
        # 初始化数据文件
        self._init_data_file()
    
    def _init_data_file(self):
        """初始化数据文件"""
        with self._lock:
            if not self.data_file.exists():
                # 获取北京时间当前日期
                beijing_now = datetime.now(self._beijing_tz)
                beijing_date = beijing_now.date()
                
                initial_data = {
                    "current_date": beijing_date.isoformat(),
                    "total_tokens": 0,
                    "last_reset": beijing_date.isoformat()
                }
                self._write_data(initial_data)
                logger.info(f"已创建用量数据文件: {self.data_file}")
    
    def _read_data(self) -> Dict:
        """读取用量数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"读取用量数据失败，重置数据: {e}")
            # 获取北京时间当前日期
            beijing_now = datetime.now(self._beijing_tz)
            beijing_date = beijing_now.date()
            return {
                "current_date": beijing_date.isoformat(),
                "total_tokens": 0,
                "last_reset": beijing_date.isoformat()
            }
    
    def _write_data(self, data: Dict):
        """写入用量数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"写入用量数据失败: {e}")
    
    def _check_and_reset_if_needed(self, data: Dict) -> Dict:
        """检查并重置过期数据（基于北京时间）"""
        # 获取当前北京时间
        beijing_now = datetime.now(self._beijing_tz)
        beijing_today = beijing_now.date()
        
        # 从数据中读取上次重置日期
        last_reset_str = data.get("last_reset")
        if last_reset_str:
            # 解析日期字符串
            last_reset_date = datetime.strptime(last_reset_str, "%Y-%m-%d").date()
            
            # 如果日期变化（基于北京时间），重置用量
            if last_reset_date < beijing_today:
                data["current_date"] = beijing_today.isoformat()
                data["total_tokens"] = 0
                data["last_reset"] = beijing_today.isoformat()
                logger.info(f"Token用量已重置，新日期: {beijing_today}")
        
        return data
    
    def can_make_request(self, tokens_needed: int) -> bool:
        """检查是否可以发起请求（未超过每日上限）"""
        with self._lock:
            data = self._read_data()
            data = self._check_and_reset_if_needed(data)
            
            max_daily = int(os.getenv("MAX_DAILY_TOKENS", 1000000))
            current_usage = data.get("total_tokens", 0)
            
            # 检查是否超出限制
            if current_usage + tokens_needed > max_daily:
                logger.warning(
                    f"Token用量已达上限: 当前{current_usage}, 需要{tokens_needed}, 上限{max_daily}"
                )
                return False
            
            return True
    
    def add_usage(self, tokens_used: int) -> int:
        """添加Token使用量"""
        with self._lock:
            data = self._read_data()
            data = self._check_and_reset_if_needed(data)
            
            # 更新使用量
            data["total_tokens"] = data.get("total_tokens", 0) + tokens_used
            self._write_data(data)
            
            logger.info(f"更新Token用量: +{tokens_used} = {data['total_tokens']}")
            return data["total_tokens"]
    
    def get_current_usage(self) -> Dict:
        """获取当前用量信息（包含重置时间）"""
        with self._lock:
            data = self._read_data()
            data = self._check_and_reset_if_needed(data)
            
            # 计算下次重置时间（北京时间次日0点）
            beijing_now = datetime.now(self._beijing_tz)
            beijing_today = beijing_now.date()
            beijing_tomorrow = beijing_today + timedelta(days=1)
            next_reset_time = self._beijing_tz.localize(
                datetime.combine(beijing_tomorrow, datetime.min.time())
            )
            
            return {
                "current_date": data.get("current_date"),
                "total_tokens": data.get("total_tokens", 0),
                "last_reset": data.get("last_reset"),
                "next_reset": next_reset_time.isoformat(),  # 返回ISO格式的时间
                "next_reset_timestamp": int(next_reset_time.timestamp() * 1000)  # 前端可用的时间戳
            }


class RequestManager:
    """请求管理器，用于处理用户请求中断"""
    
    def __init__(self):
        self._user_requests: Dict[str, bool] = {}  # user_id -> should_stop flag
        self._lock = threading.Lock()
    
    def register_request(self, user_id: str):
        """注册用户请求"""
        with self._lock:
            self._user_requests[user_id] = False
    
    def stop_request(self, user_id: str):
        """停止用户请求"""
        with self._lock:
            if user_id in self._user_requests:
                self._user_requests[user_id] = True
                logger.info(f"已标记停止用户 {user_id} 的请求")
    
    def should_stop(self, user_id: str) -> bool:
        """检查是否应该停止"""
        with self._lock:
            return self._user_requests.get(user_id, False)
    
    def clear_request(self, user_id: str):
        """清除用户请求状态"""
        with self._lock:
            if user_id in self._user_requests:
                del self._user_requests[user_id]


# 全局用量跟踪器和请求管理器实例
token_tracker = TokenUsageTracker()
request_manager = RequestManager()


class AIService:
    def __init__(self):
        """初始化AI服务，支持多种模型"""
        self.model_providers = {}
        self._setup_providers()
        
    def _estimate_tokens(self, messages: List[Dict]) -> int:
        """
        粗略估计消息的Token数
        
        Args:
            messages: 消息列表
            
        Returns:
            估计的token数量
        """
        total_tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            # 计算中文字符和英文字符
            chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            english_chars = len(content) - chinese_chars
            
            # 粗略估算
            tokens = chinese_chars * 2 + english_chars * 0.25
            total_tokens += int(tokens) + 5  # 加上角色信息的额外开销
        
        # 加上预计回复的token
        if messages:
            last_msg = messages[-1].get("content", "")
            chinese_chars = sum(1 for c in last_msg if '\u4e00' <= c <= '\u9fff')
            english_chars = len(last_msg) - chinese_chars
            reply_tokens = chinese_chars * 2 + english_chars * 0.25
            total_tokens += int(reply_tokens)
        
        return max(50, total_tokens)  # 最少50个token
    
    def _check_token_limit(self, messages: List[Dict]) -> bool:
        """
        检查Token用量是否超限
        
        Args:
            messages: 消息列表
            
        Returns:
            是否可以发起请求
        """
        estimated_tokens = self._estimate_tokens(messages)
        return token_tracker.can_make_request(estimated_tokens)
    
    def _setup_providers(self):
        """配置可用的AI模型提供商"""
        # 硅基流动平台DeepSeek-V3配置
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE", "https://api.siliconflow.cn/v1")
        model_name = os.getenv("DEFAULT_MODEL", "deepseek-ai/DeepSeek-V3")
        
        if deepseek_api_key:
            try:
                # 异步客户端（用于流式调用）
                async_client = AsyncOpenAI(
                    api_key=deepseek_api_key,
                    base_url=base_url
                )
                
                self.model_providers[model_name] = {
                    "sync_client": None,  # 不再需要同步客户端
                    "async_client": async_client,
                    "model": model_name,
                    "is_real": True
                }
                logger.info(f"已配置硅基流动平台模型: {model_name}")
            except Exception as e:
                logger.error(f"初始化硅基流动客户端失败: {e}")
        
        # 如果没有配置任何API密钥，使用模拟模式
        if not self.model_providers:
            logger.warning("没有配置任何AI API密钥，将使用模拟模式")
            self.model_providers["mock"] = {
                "sync_client": None, 
                "async_client": None, 
                "model": "mock",
                "is_real": False
            }
        
        # 始终添加模拟模式，无论是否有真实API密钥
        if "mock" not in self.model_providers:
            self.model_providers["mock"] = {
                "sync_client": None,
                "async_client": None,
                "model": "mock",
                "is_real": False
            }
            logger.info(f"已添加模拟模式提供者，当前可用模型: {list(self.model_providers.keys())}")
    
    def get_available_models(self) -> list:
        """获取可用的模型列表"""
        return list(self.model_providers.keys())
    
    def get_default_model(self) -> str:
        """获取默认模型"""
        models = self.get_available_models()
        if not models:
            return "mock"
        
        # 优先返回真实模型
        for model in models:
            if model != "mock":
                return model
        
        return models[0]
    
    async def stream_chat_completion(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        user_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        流式响应生成器
        
        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            user_id: 用户ID
            
        Yields:
            SSE格式的数据块
        """
        if model is None:
            model = self.get_default_model()
        
        # 映射前端发送的"模拟模式"到后端的"mock"
        if model == "模拟模式":
            model = "mock"
            logger.info(f"检测到前端模拟模式请求，映射为: {model}")
        
        # 检查模型是否可用
        if model not in self.model_providers:
            available_models = self.get_available_models()
            if "mock" in available_models:
                model = "mock"
            else:
                # 返回错误信息
                error_msg = f"模型 '{model}' 不可用。可用模型: {available_models}"
                yield f"data: {json.dumps({'content': error_msg, 'error': True, 'done': True}, ensure_ascii=False)}\n\n"
                return
        
        provider = self.model_providers[model]
        
        # 检查用量限制
        if not self._check_token_limit(messages):
            error_msg = "当日API用量已达上限，请明日再试"
            yield f"data: {json.dumps({'content': error_msg, 'error': True, 'done': True}, ensure_ascii=False)}\n\n"
            return
        
        # 注册用户请求
        if user_id:
            request_manager.register_request(user_id)
        
        try:
            # 模拟模式
            if model == "mock" or not provider["is_real"]:
                async for chunk in self._mock_stream_completion_generator(messages, user_id):
                    yield chunk
                return
            
            # 真实API流式调用
            async_client = provider["async_client"]
            model_name = provider["model"]
            
            stream = await async_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            full_content = ""
            
            async for chunk in stream:
                # 检查是否应该停止
                if user_id and request_manager.should_stop(user_id):
                    logger.info(f"用户 {user_id} 请求停止生成")
                    break
                
                if chunk.choices[0].delta.content is not None:
                    content_chunk = chunk.choices[0].delta.content
                    full_content += content_chunk
                    
                    # 返回SSE格式的数据
                    yield f"data: {json.dumps({'content': content_chunk, 'done': False}, ensure_ascii=False)}\n\n"
            
            # 流式响应结束
            yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
            
            # 估算token使用量
            estimated_tokens = self._estimate_tokens(messages + [{"role": "assistant", "content": full_content}])
            token_tracker.add_usage(estimated_tokens)
            
        except Exception as e:
            logger.error(f"AI流式服务调用失败: {str(e)}")
            # API调用失败时，回退到模拟模式
            error_msg = f"API调用失败: {str(e)}，已切换至模拟模式"
            yield f"data: {json.dumps({'content': error_msg, 'error': True, 'done': False}, ensure_ascii=False)}\n\n"
            
            async for chunk in self._mock_stream_completion_generator(messages, user_id, is_fallback=True):
                yield chunk
        finally:
            # 清理请求状态
            if user_id:
                request_manager.clear_request(user_id)
    
    async def _mock_stream_completion_generator(
        self, 
        messages: list, 
        user_id: str = None,
        is_fallback: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        模拟模式下的流式响应生成器
        
        Args:
            messages: 消息列表
            user_id: 用户ID
            is_fallback: 是否为API失败后的回退模式
            
        Yields:
            SSE格式的数据块
        """
        last_message = messages[-1]["content"] if messages else "你好"
        
        # 统一的模拟回复内容
        if is_fallback:
            # API调用失败时的回退模拟
            response_text = f"⚠️ API调用失败，已自动切换到模拟模式。🔧 此回复仅用于功能测试。如需真实AI回复，请检查API配置。"
        else:
            # 正常的模拟模式回复
            response_text = f"🤖 模拟模式回复（非真实AI模型）🔧 此回复仅用于开发测试。如需使用真实AI能力，请切换到真实模型。"
        
        # 将回复文本分割成句子，模拟逐句输出
        sentences = response_text.split('\n\n')
        
        for i, sentence in enumerate(sentences):
            # 检查是否应该停止
            if user_id and request_manager.should_stop(user_id):
                break
            
            # 模拟逐词输出效果，增加适当的延迟
            words = sentence.split()
            for word in words:
                if user_id and request_manager.should_stop(user_id):
                    break
                    
                await asyncio.sleep(0.03)  # 稍微降低延迟，提高响应速度
                yield f"data: {json.dumps({'content': word + ' ', 'done': False}, ensure_ascii=False)}\n\n"
            
            # 在句子之间添加换行
            if i < len(sentences) - 1:
                yield f"data: {json.dumps({'content': '\\n\\n', 'done': False}, ensure_ascii=False)}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
    
    def count_tokens(self, text: str, model: str = "deepseek-chat") -> int:
        """
        估算文本的token数量
        
        Note: 这是一个简化的估算，实际应该使用对应模型的tokenizer
        
        Args:
            text: 要估算的文本
            model: 模型名称
            
        Returns:
            估计的token数量
        """
        # 简化的估算：中文大约1个token=1-2个字，英文大约1个token=0.75个单词
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        # 粗略估算
        estimated_tokens = chinese_chars + int(other_chars * 0.3)
        
        return estimated_tokens
    
    def generate_branch_title(self, parent_message_content: str, thread_count: int, depth: int) -> str:
        """
        生成分支标题的智能函数
        
        Args:
            parent_message_content: 父消息内容
            thread_count: 线程计数
            depth: 分支深度
            
        Returns:
            生成的分支标题
        """
        # 去除多余空白
        content = parent_message_content.strip()
        
        # 规则1: 尝试智能提取
        # 提取第一个完整句子
        first_sentence_match = re.match(r'^[^。！？.!?]+[。！？.!?]', content)
        
        if first_sentence_match:
            first_sentence = first_sentence_match.group(0)
            
            # 去除疑问词、感叹词
            words_to_remove = ["请问", "你好", "那个", "这个", "什么", "怎么", "如何", "为什么", "?", "？", "!", "！"]
            cleaned = first_sentence
            for word in words_to_remove:
                cleaned = cleaned.replace(word, "")
            
            # 提取关键部分（中文字符、英文单词、数字）
            chinese_chars = re.findall(r'[\u4e00-\u9fff]+', cleaned)
            english_words = re.findall(r'[a-zA-Z]+', cleaned)
            numbers = re.findall(r'\d+', cleaned)
            
            all_parts = chinese_chars + english_words + numbers
            
            if len(all_parts) >= 2:
                # 取前2-3个部分组合
                key_parts = all_parts[:min(3, len(all_parts))]
                title = "".join(key_parts[:2]) if len(key_parts) >= 2 else key_parts[0]
                
                # 限制长度
                if len(title) <= 15 and len(title) >= 2:
                    return title
        
        # 规则2: 回退到关键词提取
        if len(content) > 0:
            # 过滤停用词
            stop_words = ["的", "了", "是", "在", "和", "与", "或", "有", "要", "能", "可以"]
            words = list(content)
            filtered_words = [word for word in words if word not in stop_words]
            
            if filtered_words:
                # 取前10个字符
                title = "".join(filtered_words[:10])
                if len(title) >= 2:
                    return title
        
        # 规则3: 最终保障
        # 根据深度使用不同前缀
        if depth == 1:
            return f"探索{thread_count}"
        elif depth == 2:
            return f"细节{thread_count}"
        else:
            return f"方案{thread_count}"
    
    def get_usage_info(self) -> Dict[str, Any]:
        """获取用量信息"""
        # 获取token跟踪器的使用情况
        usage = token_tracker.get_current_usage()
    
        # 从环境变量获取最大每日token数
        max_daily_tokens = int(os.getenv("MAX_DAILY_TOKENS", 1000000))
    
        # 计算剩余token数
        total_tokens = usage.get("total_tokens", 0)
        remaining_tokens = max(0, max_daily_tokens - total_tokens)
    
        # 确保返回所有前端需要的字段
        usage.update({
          "max_daily_tokens": max_daily_tokens,
          "remaining_tokens": remaining_tokens,
          "available_models": self.get_available_models(),
          "default_model": self.get_default_model(),
          "streaming_enabled": True  # 现在始终为True
        })
    
        return usage
    
    def stop_user_request(self, user_id: str):
        """停止用户的当前请求"""
        request_manager.stop_request(user_id)


# 创建全局AI服务实例
ai_service = AIService()