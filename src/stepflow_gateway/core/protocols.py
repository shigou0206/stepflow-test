"""
协议适配器基础类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseProtocolAdapter(ABC):
    """协议适配器基础类"""
    
    def __init__(self):
        self.protocol_name = "base"
    
    @abstractmethod
    def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行请求"""
        pass
    
    def build_url(self, base_url: str, path: str) -> str:
        """构建 URL"""
        return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    
    def add_auth_headers(self, headers: Dict[str, Any], auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """添加认证头部"""
        return headers
    
    def validate_response(self, response: Dict[str, Any], expected_schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """验证响应"""
        return {
            'valid': True,
            'errors': []
        }
    
    def close(self):
        """关闭连接"""
        pass 