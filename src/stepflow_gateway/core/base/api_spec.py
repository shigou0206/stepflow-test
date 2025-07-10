"""
API 规范抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ApiSpecification(ABC):
    """API 规范抽象基类"""
    
    @property
    @abstractmethod
    def spec_type(self) -> str:
        """规范类型 (openapi, asyncapi, graphql, etc.)"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """规范版本"""
        pass
    
    @abstractmethod
    def validate(self, content: str) -> bool:
        """验证规范内容"""
        pass
    
    @abstractmethod
    def parse(self, content: str) -> Dict[str, Any]:
        """解析规范内容"""
        pass
    
    @abstractmethod
    def extract_endpoints(self, parsed_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取端点信息"""
        pass
    
    def get_info(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """获取规范基本信息"""
        return parsed_content.get('info', {})
    
    def get_servers(self, parsed_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取服务器配置"""
        servers = parsed_content.get('servers', {})
        if isinstance(servers, dict):
            return [{'name': k, **v} for k, v in servers.items()]
        return servers
    
    def get_components(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """获取组件定义"""
        return parsed_content.get('components', {})
    
    def get_security_schemes(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """获取安全方案"""
        components = self.get_components(parsed_content)
        return components.get('securitySchemes', {})
    
    def get_schemas(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """获取模式定义"""
        components = self.get_components(parsed_content)
        return components.get('schemas', {})
    
    def normalize_endpoint(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """标准化端点信息"""
        return {
            'name': endpoint.get('name', ''),
            'type': endpoint.get('type', ''),
            'method': endpoint.get('method', ''),
            'operation_type': endpoint.get('operation_type', ''),
            'description': endpoint.get('description', ''),
            'parameters': endpoint.get('parameters', []),
            'request_schema': endpoint.get('request_schema', {}),
            'response_schema': endpoint.get('response_schema', {}),
            'security': endpoint.get('security', []),
            'tags': endpoint.get('tags', []),
            'bindings': endpoint.get('bindings', {})
        } 