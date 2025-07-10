"""
基础协议适配器抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable


class BaseProtocolAdapter(ABC):
    """协议适配器基类"""
    
    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """协议名称"""
        pass
    
    @abstractmethod
    def supports_protocol(self, protocol: str) -> bool:
        """检查是否支持协议"""
        pass
    
    @abstractmethod
    async def connect(self, protocol: str, config: Dict[str, Any]) -> str:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self, connection_id: str):
        """断开连接"""
        pass
    
    @abstractmethod
    async def send_message(self, connection_id: str, channel: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息"""
        pass
    
    @abstractmethod
    async def subscribe(self, connection_id: str, channel: str, handler: Callable) -> str:
        """订阅通道"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str):
        """取消订阅"""
        pass
    
    @abstractmethod
    def get_connections(self) -> List[Dict[str, Any]]:
        """获取连接列表"""
        pass
    
    @abstractmethod
    def get_subscriptions(self) -> List[Dict[str, Any]]:
        """获取订阅列表"""
        pass
    
    @abstractmethod
    async def close_all(self):
        """关闭所有连接"""
        pass 