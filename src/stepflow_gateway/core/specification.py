"""
API 规范基础类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class ApiSpecification(ABC):
    """API 规范基础类"""
    
    def __init__(self, spec_id: str, name: str, spec_type: str, content: Dict[str, Any], version: str = "1.0.0"):
        self.spec_id = spec_id
        self.name = name
        self.spec_type = spec_type
        self.content = content
        self.version = version
        self.status = "active"
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    @abstractmethod
    def validate(self) -> bool:
        """验证规范"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取规范信息"""
        return self.content.get('info', {})
    
    def get_servers(self) -> List[Dict[str, Any]]:
        """获取服务器配置"""
        return self.content.get('servers', [])
    
    def get_components(self) -> Dict[str, Any]:
        """获取组件定义"""
        return self.content.get('components', {})
    
    def get_security_schemes(self) -> Dict[str, Any]:
        """获取安全方案"""
        components = self.get_components()
        return components.get('securitySchemes', {})
    
    def get_global_security(self) -> List[Dict[str, Any]]:
        """获取全局安全配置"""
        return self.content.get('security', [])
    
    def resolve_reference(self, ref: str) -> Optional[Dict[str, Any]]:
        """解析引用"""
        if not ref.startswith('#/'):
            return None
        
        # 移除开头的 '#/'
        path = ref[2:]
        parts = path.split('/')
        
        current = self.content
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'spec_id': self.spec_id,
            'name': self.name,
            'spec_type': self.spec_type,
            'version': self.version,
            'content': self.content,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApiSpecification':
        """从字典创建实例"""
        spec = cls(
            spec_id=data['spec_id'],
            name=data['name'],
            spec_type=data['spec_type'],
            content=data['content'],
            version=data.get('version', '1.0.0')
        )
        spec.status = data.get('status', 'active')
        spec.created_at = data.get('created_at', datetime.now().isoformat())
        spec.updated_at = data.get('updated_at', datetime.now().isoformat())
        return spec 