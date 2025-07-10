"""
AsyncAPI 解析器
"""

import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from ...core.base.parser import BaseParser
from .specification import AsyncAPISpecification


class AsyncAPIParser(BaseParser):
    """AsyncAPI 解析器实现"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.supported_versions = ['2.0.0', '2.1.0', '2.2.0', '2.3.0', '2.4.0', '2.5.0', '2.6.0']
    
    def can_parse(self, content: str) -> bool:
        """检查是否可以解析内容"""
        try:
            if isinstance(content, str):
                data = json.loads(content)
            elif isinstance(content, dict):
                data = content
            else:
                return False
            
            # 检查是否是 AsyncAPI 规范
            asyncapi_version = data.get('asyncapi', '')
            if not asyncapi_version.startswith('2.'):
                return False
            
            # 检查必需字段
            required_fields = ['info', 'channels']
            for field in required_fields:
                if field not in data:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def validate(self, content: str) -> bool:
        """验证内容"""
        try:
            if isinstance(content, str):
                data = json.loads(content)
            elif isinstance(content, dict):
                data = content
            else:
                return False
            
            # 检查是否是 AsyncAPI 规范
            asyncapi_version = data.get('asyncapi', '')
            if not asyncapi_version.startswith('2.'):
                return False
            
            # 检查必需字段
            required_fields = ['info', 'channels']
            for field in required_fields:
                if field not in data:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def parse(self, content: str, spec_id: str = None, name: str = None) -> AsyncAPISpecification:
        """解析 AsyncAPI 内容"""
        try:
            # 解析内容
            if isinstance(content, str):
                parsed_content = json.loads(content)
            elif isinstance(content, dict):
                parsed_content = content
            else:
                raise ValueError("内容必须是字符串或字典")
            
            # 验证版本
            asyncapi_version = parsed_content.get('asyncapi', '')
            if not asyncapi_version.startswith('2.'):
                raise ValueError(f"不支持的 AsyncAPI 版本: {asyncapi_version}")
            
            # 创建规范实例
            spec = AsyncAPISpecification(
                spec_id=spec_id,
                name=name or parsed_content.get('info', {}).get('title', 'Untitled AsyncAPI'),
                content=parsed_content,
                version=asyncapi_version
            )
            
            # 验证规范
            if not spec.validate():
                raise ValueError("AsyncAPI 规范验证失败")
            
            self.logger.info(f"成功解析 AsyncAPI 规范: {spec.name}")
            return spec
            
        except Exception as e:
            self.logger.error(f"解析 AsyncAPI 内容失败: {e}")
            raise
    
    def extract_endpoints(self, spec: AsyncAPISpecification) -> List[Dict[str, Any]]:
        """提取端点信息"""
        try:
            endpoints = []
            channels = spec.get_channels()
            
            for channel_name, channel_item in channels.items():
                # 处理发布操作
                if 'publish' in channel_item:
                    publish_op = channel_item['publish']
                    endpoint = self._create_endpoint(
                        spec, channel_name, 'publish', publish_op, channel_item
                    )
                    endpoints.append(endpoint)
                
                # 处理订阅操作
                if 'subscribe' in channel_item:
                    subscribe_op = channel_item['subscribe']
                    endpoint = self._create_endpoint(
                        spec, channel_name, 'subscribe', subscribe_op, channel_item
                    )
                    endpoints.append(endpoint)
            
            self.logger.info(f"从 AsyncAPI 规范中提取了 {len(endpoints)} 个端点")
            return endpoints
            
        except Exception as e:
            self.logger.error(f"提取端点失败: {e}")
            raise
    
    def _create_endpoint(self, spec: AsyncAPISpecification, channel_name: str, 
                        operation_type: str, operation: Dict[str, Any], 
                        channel_item: Dict[str, Any]) -> Dict[str, Any]:
        """创建端点信息"""
        # 解析消息模式
        message_schema = self._parse_message_schema(spec, operation)
        
        # 解析参数
        parameters = self._parse_parameters(spec, channel_item)
        
        # 解析安全方案
        security = self._parse_security(spec, channel_item)
        
        # 获取协议信息
        protocol = self._get_protocol(channel_item)
        
        # 获取服务器信息
        servers = self._get_servers(spec, protocol)
        
        endpoint = {
            'name': f"{operation_type.upper()} {channel_name}",
            'type': 'async',
            'method': operation_type.upper(),
            'operation_type': operation_type.lower(),
            'description': operation.get('summary', ''),
            'parameters': parameters,
            'request_schema': message_schema,
            'response_schema': operation.get('traits', {}),
            'security': security,
            'tags': operation.get('tags', []),
            'channel_name': channel_name,
            'protocol': protocol,
            'servers': servers,
            'operation_id': operation.get('operationId', ''),
            'bindings': channel_item.get('bindings', {}),
            'message': operation.get('message', {}),
            'traits': operation.get('traits', [])
        }
        
        return endpoint
    
    def _parse_message_schema(self, spec: AsyncAPISpecification, operation: Dict[str, Any]) -> Dict[str, Any]:
        """解析消息模式"""
        message = operation.get('message', {})
        
        if isinstance(message, dict):
            # 直接定义的消息
            return {
                'type': 'object',
                'properties': message.get('payload', {}),
                'headers': message.get('headers', {}),
                'correlationId': message.get('correlationId', {}),
                'contentType': message.get('contentType', 'application/json'),
                'name': message.get('name', ''),
                'title': message.get('title', ''),
                'summary': message.get('summary', ''),
                'description': message.get('description', '')
            }
        elif isinstance(message, str):
            # 引用消息
            if message.startswith('#/components/messages/'):
                message_name = message.split('/')[-1]
                messages = spec.get_messages()
                if message_name in messages:
                    return self._parse_message_schema(spec, {'message': messages[message_name]})
        
        return {}
    
    def _parse_parameters(self, spec: AsyncAPISpecification, channel_item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析参数"""
        parameters = []
        
        # 通道参数
        if 'parameters' in channel_item:
            for param_name, param_def in channel_item['parameters'].items():
                param = {
                    'name': param_name,
                    'in': 'channel',
                    'required': param_def.get('required', False),
                    'schema': param_def.get('schema', {}),
                    'description': param_def.get('description', ''),
                    'location': param_def.get('location', '')
                }
                parameters.append(param)
        
        return parameters
    
    def _parse_security(self, spec: AsyncAPISpecification, channel_item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析安全方案"""
        security = []
        
        # 通道级安全
        if 'security' in channel_item:
            security.extend(channel_item['security'])
        
        # 绑定安全
        bindings = channel_item.get('bindings', {})
        for protocol, binding in bindings.items():
            if 'security' in binding:
                security.extend(binding['security'])
        
        return security
    
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
        elif 'http' in bindings:
            return 'http'
        elif 'ibmmq' in bindings:
            return 'ibmmq'
        else:
            return 'unknown'
    
    def _get_servers(self, spec: AsyncAPISpecification, protocol: str) -> List[Dict[str, Any]]:
        """获取服务器配置"""
        servers = spec.get_servers()
        protocol_servers = []
        
        for server_name, server_config in servers.items():
            # 检查服务器是否支持指定协议
            if self._server_supports_protocol(server_config, protocol):
                server_info = {
                    'name': server_name,
                    'url': server_config.get('url', ''),
                    'protocol': server_config.get('protocol', protocol),
                    'description': server_config.get('description', ''),
                    'variables': server_config.get('variables', {}),
                    'security': server_config.get('security', [])
                }
                protocol_servers.append(server_info)
        
        return protocol_servers
    
    def _server_supports_protocol(self, server_config: Dict[str, Any], protocol: str) -> bool:
        """检查服务器是否支持指定协议"""
        server_protocol = server_config.get('protocol', '').lower()
        
        # 协议映射
        protocol_mapping = {
            'websocket': ['ws', 'wss', 'websocket'],
            'mqtt': ['mqtt', 'mqtts'],
            'amqp': ['amqp', 'amqps'],
            'kafka': ['kafka'],
            'nats': ['nats', 'nats-secure'],
            'http': ['http', 'https'],
            'ibmmq': ['ibmmq']
        }
        
        if protocol in protocol_mapping:
            return server_protocol in protocol_mapping[protocol]
        
        return True  # 如果协议未知，假设支持
    
    def parse_from_file(self, file_path: str, spec_id: str = None, name: str = None) -> AsyncAPISpecification:
        """从文件解析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse(content, spec_id, name)
            
        except Exception as e:
            self.logger.error(f"从文件解析失败: {e}")
            raise
    
    def parse_from_url(self, url: str, spec_id: str = None, name: str = None) -> AsyncAPISpecification:
        """从 URL 解析"""
        try:
            import requests
            
            response = requests.get(url)
            response.raise_for_status()
            
            content = response.text
            return self.parse(content, spec_id, name)
            
        except Exception as e:
            self.logger.error(f"从 URL 解析失败: {e}")
            raise
    
    def validate_schema(self, schema: Dict[str, Any]) -> bool:
        """验证模式"""
        try:
            # 基本结构验证
            if not isinstance(schema, dict):
                return False
            
            # 检查必需字段
            if 'type' not in schema:
                return False
            
            # 验证类型
            valid_types = ['object', 'array', 'string', 'number', 'integer', 'boolean', 'null']
            if schema['type'] not in valid_types:
                return False
            
            # 验证属性
            if 'properties' in schema:
                if not isinstance(schema['properties'], dict):
                    return False
            
            # 验证必需字段
            if 'required' in schema:
                if not isinstance(schema['required'], list):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def resolve_references(self, spec: AsyncAPISpecification, obj: Dict[str, Any]) -> Dict[str, Any]:
        """解析引用"""
        if isinstance(obj, dict):
            resolved = {}
            for key, value in obj.items():
                if key == '$ref' and isinstance(value, str):
                    resolved_value = spec.resolve_reference(value)
                    if resolved_value:
                        resolved.update(resolved_value)
                else:
                    resolved[key] = self.resolve_references(spec, value)
            return resolved
        elif isinstance(obj, list):
            return [self.resolve_references(spec, item) for item in obj]
        else:
            return obj 