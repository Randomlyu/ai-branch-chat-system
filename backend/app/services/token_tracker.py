"""
Token用量跟踪器
用于管理应用级全局每日Token用量限制
"""
import json
import os
import threading
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TokenUsageTracker:
    """Token用量跟踪器，使用文件存储保证重启后数据不丢失"""
    
    def __init__(self, data_file: str = "token_usage.json"):
        """
        初始化用量跟踪器
        
        Args:
            data_file: 存储用量数据的JSON文件路径
        """
        self.data_file = Path(data_file)
        self._lock = threading.Lock()
        self._usage_data: Optional[Dict] = None
        
        # 初始化数据文件
        self._init_data_file()
    
    def _init_data_file(self):
        """初始化数据文件"""
        with self._lock:
            if not self.data_file.exists():
                initial_data = {
                    "current_date": date.today().isoformat(),
                    "total_tokens": 0,
                    "last_reset": date.today().isoformat()
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
            return {
                "current_date": date.today().isoformat(),
                "total_tokens": 0,
                "last_reset": date.today().isoformat()
            }
    
    def _write_data(self, data: Dict):
        """写入用量数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"写入用量数据失败: {e}")
    
    def _check_and_reset_if_needed(self, data: Dict) -> Dict:
        """检查并重置过期数据"""
        today = date.today()
        last_reset = datetime.strptime(data["last_reset"], "%Y-%m-%d").date()
        
        # 如果日期变化，重置用量
        if last_reset < today:
            data["current_date"] = today.isoformat()
            data["total_tokens"] = 0
            data["last_reset"] = today.isoformat()
            logger.info(f"Token用量已重置，新日期: {today}")
        
        return data
    
    def can_make_request(self, tokens_needed: int) -> bool:
        """
        检查是否可以发起请求（未超过每日上限）
        
        Args:
            tokens_needed: 本次请求预计需要的Token数
            
        Returns:
            是否允许请求
        """
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
        """
        添加Token使用量
        
        Args:
            tokens_used: 使用的Token数
            
        Returns:
            更新后的总使用量
        """
        with self._lock:
            data = self._read_data()
            data = self._check_and_reset_if_needed(data)
            
            # 更新使用量
            data["total_tokens"] = data.get("total_tokens", 0) + tokens_used
            self._write_data(data)
            
            logger.info(f"更新Token用量: +{tokens_used} = {data['total_tokens']}")
            return data["total_tokens"]
    
    def get_current_usage(self) -> Dict:
        """获取当前用量信息"""
        with self._lock:
            data = self._read_data()
            data = self._check_and_reset_if_needed(data)
            
            return {
                "current_date": data["current_date"],
                "total_tokens": data.get("total_tokens", 0),
                "max_daily_tokens": int(os.getenv("MAX_DAILY_TOKENS", 1000000)),
                "remaining_tokens": max(0, int(os.getenv("MAX_DAILY_TOKENS", 1000000)) - data.get("total_tokens", 0))
            }
    
    def reset_usage(self) -> Dict:
        """手动重置用量（用于测试）"""
        with self._lock:
            today = date.today()
            data = {
                "current_date": today.isoformat(),
                "total_tokens": 0,
                "last_reset": today.isoformat()
            }
            self._write_data(data)
            logger.info("Token用量已手动重置")
            return data


# 全局用量跟踪器实例
token_tracker = TokenUsageTracker()


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
                logger.debug(f"已清除用户 {user_id} 的请求状态")


# 全局请求管理器实例
request_manager = RequestManager()