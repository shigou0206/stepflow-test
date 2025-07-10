"""
AsyncAPI 规范类
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from ...core.base.api_spec import ApiSpecification


class AsyncAPISpecification(ApiSpecification):
    """AsyncAPI 规范实现"""
    
    def __init__(self, spec_id: str = None, name: str = None, content: Dict[str, Any] = None, version: str = "2.0.0"):
        self.spec_id = spec_id or str(uuid.uuid4())
        self.name = name or "Untitled AsyncAPI"
        self.content = content or {}
        # 优先从 content 里获取 asyncapi 字段
        self._version = (self.content.get("asyncapi") or version)
        self.status = "active"
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.logger = logging.getLogger(__name__)
    
    @property
    def spec_type(self) -> str:
        """规范类型"""
        return "asyncapi"
    
    @property
    def version(self) -> str:
        """规范版本"""
        return self._version
    
    def validate(self, content: str = None) -> bool:
        """验证 AsyncAPI 规范"""
        try:
            # 使用传入的内容或实例内容
            spec_content = content or self.content
            
            # 基本结构验证
            if not isinstance(spec_content, dict):
                self.logger.error("AsyncAPI 内容必须是字典格式")
                return False
            
            # 检查必需字段
            required_fields = ['asyncapi', 'info', 'channels']
            for field in required_fields:
                if field not in spec_content:
                    self.logger.error(f"缺少必需字段: {field}")
                    return False
            
            # 验证 asyncapi 版本
            asyncapi_version = spec_content.get('asyncapi', '')
            if not asyncapi_version.startswith('2.'):
                self.logger.error(f"不支持的 AsyncAPI 版本: {asyncapi_version}")
                return False
            
            # 验证 info 对象
            info = spec_content.get('info', {})
            if not isinstance(info, dict) or 'title' not in info:
                self.logger.error("info 对象必须包含 title 字段")
                return False
            
            # 验证 channels 对象
            channels = spec_content.get('channels', {})
            if not isinstance(channels, dict):
                self.logger.error("channels 必须是字典格式")
                return False
            
            # 验证每个通道
            for channel_name, channel_item in channels.items():
                if not isinstance(channel_item, dict):
                    self.logger.error(f"通道 {channel_name} 必须是字典格式")
                    return False
                
                # 检查是否有发布或订阅操作
                has_publish = 'publish' in channel_item
                has_subscribe = 'subscribe' in channel_item
                
                if not has_publish and not has_subscribe:
                    self.logger.warning(f"通道 {channel_name} 没有定义发布或订阅操作")
            
            self.logger.info(f"AsyncAPI 规范验证通过: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"AsyncAPI 规范验证失败: {e}")
            return False
    
    def parse(self, content: str) -> Dict[str, Any]:
        """解析规范内容"""
        try:
            if isinstance(content, str):
                return json.loads(content)
            elif isinstance(content, dict):
                return content
            else:
                raise ValueError("内容必须是字符串或字典")
        except Exception as e:
            self.logger.error(f"解析规范内容失败: {e}")
            raise
    
    def extract_endpoints(self, parsed_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取端点信息（通道和操作）"""
        endpoints = []
        channels = parsed_content.get('channels', {})
        
        for channel_name, channel_item in channels.items():
            # 处理发布操作
            if 'publish' in channel_item:
                publish_op = channel_item['publish']
                endpoint = self._create_endpoint(
                    channel_name, 'publish', publish_op, channel_item
                )
                endpoints.append(endpoint)
            
            # 处理订阅操作
            if 'subscribe' in channel_item:
                subscribe_op = channel_item['subscribe']
                endpoint = self._create_endpoint(
                    channel_name, 'subscribe', subscribe_op, channel_item
                )
                endpoints.append(endpoint)
        
        return endpoints
    
    def _create_endpoint(self, channel_name: str, operation_type: str, 
                        operation: Dict[str, Any], channel_item: Dict[str, Any]) -> Dict[str, Any]:
        """创建端点信息"""
        return {
            'name': f"{operation_type.upper()} {channel_name}",
            'type': 'async',
            'method': operation_type.upper(),
            'operation_type': operation_type.lower(),
            'description': operation.get('summary', ''),
            'parameters': self._extract_parameters(channel_item),
            'request_schema': operation.get('message', {}),
            'response_schema': operation.get('traits', {}),
            'security': channel_item.get('bindings', {}),
            'tags': operation.get('tags', []),
            'channel_name': channel_name,
            'protocol': self._get_protocol(channel_item)
        }
    
    def _extract_parameters(self, channel_item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取通道参数"""
        parameters = []
        
        # 通道参数
        if 'parameters' in channel_item:
            for param_name, param_def in channel_item['parameters'].items():
                param = {
                    'name': param_name,
                    'in': 'channel',
                    'required': param_def.get('required', False),
                    'schema': param_def.get('schema', {}),
                    'description': param_def.get('description', '')
                }
                parameters.append(param)
        
        return parameters
    
    def _get_protocol(self, channel_item: Dict[str, Any]) -> str:
        """获取协议类型"""
        bindings = channel_item.get('bindings', {})
        
        # 检查各种协议绑定
        if 'websockets' in bindings:
            return 'websocket'
        elif 'mqtt' in bindings:
            return 'mqtt'
        elif 'amqp' in bindings:
            return 'amqp'
        elif 'kafka' in bindings:
            return 'kafka'
        elif 'nats' in bindings:
            return 'nats'
        else:
            return 'unknown'
    
    # AsyncAPI 特定方法
    def get_info(self) -> Dict[str, Any]:
        """获取规范信息"""
        info = self.content.get('info', {})
        return {
            'title': info.get('title', ''),
            'description': info.get('description', ''),
            'version': info.get('version', ''),
            'contact': info.get('contact', {}),
            'license': info.get('license', {}),
            'servers': self.content.get('servers', {}),
            'asyncapi_version': self.content.get('asyncapi', ''),
            'spec_type': self.spec_type,
            'spec_id': self.spec_id,
            'name': self.name
        }
    
    def get_servers(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return self.content.get('servers', {})
    
    def get_channels(self) -> Dict[str, Any]:
        """获取通道定义"""
        return self.content.get('channels', {})
    
    def get_components(self) -> Dict[str, Any]:
        """获取组件定义"""
        return self.content.get('components', {})
    
    def get_messages(self) -> Dict[str, Any]:
        """获取消息定义"""
        components = self.get_components()
        return components.get('messages', {})
    
    def get_schemas(self) -> Dict[str, Any]:
        """获取模式定义"""
        components = self.get_components()
        return components.get('schemas', {})
    
    def get_security_schemes(self) -> Dict[str, Any]:
        """获取安全方案"""
        components = self.get_components()
        return components.get('securitySchemes', {})
    
    def get_channel(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """获取特定通道"""
        channels = self.get_channels()
        return channels.get(channel_name)
    
    def get_operation(self, channel_name: str, operation_type: str) -> Optional[Dict[str, Any]]:
        """获取特定操作"""
        channel = self.get_channel(channel_name)
        if channel:
            return channel.get(operation_type)
        return None
    
    def get_message_schema(self, message_ref: str) -> Optional[Dict[str, Any]]:
        """获取消息模式"""
        messages = self.get_messages()
        if message_ref in messages:
            return messages[message_ref].get('payload', {})
        return None
    
    def resolve_reference(self, ref: str) -> Optional[Dict[str, Any]]:
        """解析引用"""
        if ref.startswith('#/components/'):
            parts = ref.split('/')
            if len(parts) >= 4:
                component_type = parts[2]
                component_name = parts[3]
                
                components = self.get_components()
                if component_type in components:
                    return components[component_type].get(component_name)
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'spec_id': self.spec_id,
            'name': self.name,
            'content': self.content,
            'version': self._version,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'spec_type': self.spec_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AsyncAPISpecification':
        """从字典创建实例"""
        return cls(
            spec_id=data.get('spec_id'),
            name=data.get('name'),
            content=data.get('content', {}),
            version=data.get('version', '2.0.0')
        )
    
    @classmethod
    def from_file(cls, file_path: str, spec_id: str = None, name: str = None) -> 'AsyncAPISpecification':
        """从文件创建实例"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        return cls(
            spec_id=spec_id,
            name=name,
            content=content
        ) 