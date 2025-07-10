"""
协议适配器抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
import logging
import asyncio
from datetime import datetime


class BaseProtocolAdapter(ABC):
    """协议适配器抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._connected = False
        self._connection_info = {}
    
    @property
    def protocol_name(self) -> str:
        """协议名称"""
        name = self.__class__.__name__.replace('Adapter', '').lower()
        # 处理 TestProtocol -> test 的情况
        if name == 'test':
            return 'test'
        return name
    
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected
    
    @abstractmethod
    async def connect(self, config: Dict[str, Any] = None):
        """建立连接"""
        pass
    
    @abstractmethod
    async def execute(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行操作"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            'protocol': self.protocol_name,
            'connected': self._connected,
            'config': self.config,
            'connection_info': self._connection_info,
            'timestamp': datetime.now().isoformat()
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        # 子类可以重写此方法来实现具体的配置验证
        return True
    
    def get_supported_operations(self) -> List[str]:
        """获取支持的操作"""
        # 子类可以重写此方法来返回支持的操作列表
        return []
    
    def get_operation_schema(self, operation: str) -> Dict[str, Any]:
        """获取操作的模式定义"""
        # 子类可以重写此方法来返回操作的模式定义
        return {}
    
    def validate_operation_data(self, operation: str, data: Dict[str, Any]) -> bool:
        """验证操作数据"""
        # 子类可以重写此方法来实现具体的数据验证
        return True
    
    def transform_request(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """转换请求数据"""
        # 子类可以重写此方法来实现请求数据转换
        return data
    
    def transform_response(self, operation: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """转换响应数据"""
        # 子类可以重写此方法来实现响应数据转换
        return response
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """处理错误"""
        self.logger.error(f"Protocol error: {error}")
        return {
            'success': False,
            'error': str(error),
            'protocol': self.protocol_name,
            'timestamp': datetime.now().isoformat()
        }
    
    def log_operation(self, operation: str, data: Dict[str, Any], response: Dict[str, Any]):
        """记录操作日志"""
        self.logger.info(f"Operation: {operation}, Data: {data}, Response: {response}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取协议适配器指标"""
        return {
            'protocol': self.protocol_name,
            'connected': self._connected,
            'supported_operations': self.get_supported_operations(),
            'timestamp': datetime.now().isoformat()
        }


class ProtocolManager:
    """协议管理器"""
    
    def __init__(self):
        self._adapters = {}
        self._connections = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_adapter(self, protocol_name: str, adapter_class: type):
        """注册协议适配器"""
        self._adapters[protocol_name] = adapter_class
        self.logger.info(f"Registered protocol adapter: {protocol_name}")
    
    def get_adapter(self, protocol_name: str) -> Optional[type]:
        """获取协议适配器类"""
        return self._adapters.get(protocol_name)
    
    async def create_connection(self, protocol_name: str, config: Dict[str, Any]) -> Optional[BaseProtocolAdapter]:
        """创建连接"""
        adapter_class = self.get_adapter(protocol_name)
        if not adapter_class:
            self.logger.error(f"Protocol adapter not found: {protocol_name}")
            return None
        
        try:
            adapter = adapter_class(config)
            await adapter.connect(config)
            
            connection_id = f"{protocol_name}_{len(self._connections)}"
            self._connections[connection_id] = adapter
            
            self.logger.info(f"Created connection: {connection_id}")
            return adapter
            
        except Exception as e:
            self.logger.error(f"Failed to create connection for {protocol_name}: {e}")
            return None
    
    def get_connection(self, connection_id: str) -> Optional[BaseProtocolAdapter]:
        """获取连接"""
        return self._connections.get(connection_id)
    
    async def close_connection(self, connection_id: str):
        """关闭连接"""
        adapter = self._connections.get(connection_id)
        if adapter:
            try:
                await adapter.disconnect()
                del self._connections[connection_id]
                self.logger.info(f"Closed connection: {connection_id}")
            except Exception as e:
                self.logger.error(f"Failed to close connection {connection_id}: {e}")
    
    async def close_all_connections(self):
        """关闭所有连接"""
        for connection_id in list(self._connections.keys()):
            await self.close_connection(connection_id)
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """列出所有连接"""
        connections = []
        for connection_id, adapter in self._connections.items():
            connections.append({
                'connection_id': connection_id,
                'protocol': adapter.protocol_name,
                'connected': adapter.is_connected,
                'connection_info': adapter.get_connection_info()
            })
        return connections
    
    def get_supported_protocols(self) -> List[str]:
        """获取支持的协议列表"""
        return list(self._adapters.keys())
    
    def get_protocol_info(self, protocol_name: str) -> Dict[str, Any]:
        """获取协议信息"""
        adapter_class = self.get_adapter(protocol_name)
        if not adapter_class:
            return {}
        
        # 创建临时实例来获取协议信息
        temp_config = {}
        temp_adapter = adapter_class(temp_config)
        
        return {
            'protocol_name': protocol_name,
            'supported_operations': temp_adapter.get_supported_operations(),
            'config_schema': temp_adapter.get_operation_schema('config')
        } 