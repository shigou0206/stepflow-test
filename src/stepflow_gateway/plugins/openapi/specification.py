"""
OpenAPI 规范类
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from ...core.base.api_spec import ApiSpecification


class OpenAPISpecification(ApiSpecification):
    """OpenAPI 规范实现"""
    
    def __init__(self, spec_id: str = None, name: str = None, content: Dict[str, Any] = None, version: str = "3.0.0"):
        self.spec_id = spec_id or str(uuid.uuid4())
        self.name = name or "Untitled API"
        self.content = content or {}
        self._version = version
        self.status = "active"
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.logger = logging.getLogger(__name__)
    
    @property
    def spec_type(self) -> str:
        """规范类型"""
        return "openapi"
    
    @property
    def version(self) -> str:
        """规范版本"""
        return self._version
    
    def validate(self, content: str = None) -> bool:
        """验证 OpenAPI 规范"""
        try:
            # 使用传入的内容或实例内容
            spec_content = content or self.content
            
            # 基本结构验证
            if not isinstance(spec_content, dict):
                self.logger.error("OpenAPI 内容必须是字典格式")
                return False
            
            # 检查必需字段
            required_fields = ['openapi', 'info', 'paths']
            for field in required_fields:
                if field not in spec_content:
                    self.logger.error(f"缺少必需字段: {field}")
                    return False
            
            # 验证 openapi 版本
            openapi_version = spec_content.get('openapi', '')
            if not openapi_version.startswith('3.'):
                self.logger.error(f"不支持的 OpenAPI 版本: {openapi_version}")
                return False
            
            # 验证 info 对象
            info = spec_content.get('info', {})
            if not isinstance(info, dict) or 'title' not in info:
                self.logger.error("info 对象必须包含 title 字段")
                return False
            
            # 验证 paths 对象
            paths = spec_content.get('paths', {})
            if not isinstance(paths, dict):
                self.logger.error("paths 必须是字典格式")
                return False
            
            # 验证每个路径
            for path, path_item in paths.items():
                if not isinstance(path_item, dict):
                    self.logger.error(f"路径 {path} 必须是字典格式")
                    return False
                
                # 检查是否有 HTTP 方法
                http_methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace']
                has_method = any(method in path_item for method in http_methods)
                if not has_method:
                    self.logger.warning(f"路径 {path} 没有定义 HTTP 方法")
            
            self.logger.info(f"OpenAPI 规范验证通过: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"OpenAPI 规范验证失败: {e}")
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
        """提取端点信息"""
        endpoints = []
        paths = parsed_content.get('paths', {})
        
        for path, path_item in paths.items():
            # 获取路径级别的参数
            path_params = path_item.get('parameters', [])
            
            # 处理每个 HTTP 方法
            http_methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace']
            
            for method in http_methods:
                if method in path_item:
                    operation = path_item[method]
                    
                    # 合并参数
                    operation_params = operation.get('parameters', [])
                    all_params = self._merge_parameters(path_params, operation_params)
                    
                    endpoint = {
                        'name': f"{method.upper()} {path}",
                        'type': 'http',
                        'method': method.upper(),
                        'operation_type': method.lower(),
                        'description': operation.get('summary', ''),
                        'parameters': all_params,
                        'request_schema': operation.get('requestBody', {}),
                        'response_schema': operation.get('responses', {}),
                        'security': operation.get('security', []),
                        'tags': operation.get('tags', [])
                    }
                    
                    endpoints.append(self.normalize_endpoint(endpoint))
        
        return endpoints
    
    def _merge_parameters(self, path_params: List[Dict[str, Any]], 
                         operation_params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并参数，操作参数优先"""
        param_map = {}
        
        # 先添加路径参数
        for param in path_params:
            param_map[param.get('name')] = param
        
        # 操作参数覆盖路径参数
        for param in operation_params:
            param_map[param.get('name')] = param
        
        return list(param_map.values())
    
    # 额外的 OpenAPI 特定方法
    def get_info(self) -> Dict[str, Any]:
        """获取规范信息"""
        info = self.content.get('info', {})
        return {
            'title': info.get('title', ''),
            'description': info.get('description', ''),
            'version': info.get('version', ''),
            'contact': info.get('contact', {}),
            'license': info.get('license', {}),
            'servers': self.content.get('servers', []),
            'openapi_version': self.content.get('openapi', ''),
            'spec_type': self.spec_type,
            'spec_id': self.spec_id,
            'name': self.name
        }
    
    def get_servers(self) -> List[Dict[str, Any]]:
        """获取服务器配置"""
        return self.content.get('servers', [])
    
    def get_paths(self) -> Dict[str, Any]:
        """获取路径定义"""
        return self.content.get('paths', {})
    
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
    
    def get_operation(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """获取特定操作"""
        paths = self.get_paths()
        path_item = paths.get(path, {})
        return path_item.get(method.lower())
    
    def get_operation_parameters(self, path: str, method: str) -> List[Dict[str, Any]]:
        """获取操作参数"""
        operation = self.get_operation(path, method)
        if not operation:
            return []
        
        # 合并路径参数和操作参数
        path_item = self.get_paths().get(path, {})
        path_params = path_item.get('parameters', [])
        operation_params = operation.get('parameters', [])
        
        # 去重，操作参数优先
        param_map = {}
        for param in path_params:
            param_map[param.get('name')] = param
        
        for param in operation_params:
            param_map[param.get('name')] = param
        
        return list(param_map.values())
    
    def get_operation_security(self, path: str, method: str) -> List[Dict[str, Any]]:
        """获取操作安全配置"""
        operation = self.get_operation(path, method)
        if not operation:
            return self.get_global_security()
        
        return operation.get('security', self.get_global_security())
    
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
    
    def get_schema(self, schema_ref: str) -> Optional[Dict[str, Any]]:
        """获取模式定义"""
        if schema_ref.startswith('#/components/schemas/'):
            schema_name = schema_ref.split('/')[-1]
            components = self.get_components()
            schemas = components.get('schemas', {})
            return schemas.get(schema_name)
        
        return self.resolve_reference(schema_ref)
    
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
    def from_dict(cls, data: Dict[str, Any]) -> 'OpenAPISpecification':
        """从字典创建实例"""
        spec = cls(
            spec_id=data['spec_id'],
            name=data['name'],
            content=data['content'],
            version=data.get('version', '3.0.0')
        )
        spec.status = data.get('status', 'active')
        spec.created_at = data.get('created_at', datetime.now().isoformat())
        spec.updated_at = data.get('updated_at', datetime.now().isoformat())
        return spec
    
    @classmethod
    def from_file(cls, file_path: str, spec_id: str = None, name: str = None) -> 'OpenAPISpecification':
        """从文件创建实例"""
        import json
        import yaml
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析为 JSON
        try:
            spec_content = json.loads(content)
        except json.JSONDecodeError:
            # 尝试解析为 YAML
            try:
                spec_content = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ValueError(f"无法解析文件格式: {e}")
        
        if not spec_id:
            spec_id = str(uuid.uuid4())
        
        if not name:
            info = spec_content.get('info', {})
            name = info.get('title', 'Untitled API')
        
        return cls(spec_id, name, spec_content) 