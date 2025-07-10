"""
OpenAPI 解析器
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid

from ...core.base.parser import BaseParser
from .specification import OpenAPISpecification


class OpenAPIParser(BaseParser):
    """OpenAPI 解析器实现"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def parse(self, content: str) -> Dict[str, Any]:
        """解析 OpenAPI 内容"""
        try:
            # 使用父类的解析方法
            return self.parse_content(content)
        except Exception as e:
            self.logger.error(f"解析 OpenAPI 内容失败: {e}")
            raise
    
    def validate(self, content: str) -> bool:
        """验证 OpenAPI 内容"""
        try:
            # 解析内容
            parsed_content = self.parse_content(content)
            
            # 基本结构验证
            if not isinstance(parsed_content, dict):
                return False
            
            # 检查必需字段
            required_fields = ['openapi', 'info', 'paths']
            for field in required_fields:
                if field not in parsed_content:
                    return False
            
            # 验证 openapi 版本
            openapi_version = parsed_content.get('openapi', '')
            if not openapi_version.startswith('3.'):
                return False
            
            # 验证 info 对象
            info = parsed_content.get('info', {})
            if not isinstance(info, dict) or 'title' not in info:
                return False
            
            # 验证 paths 对象
            paths = parsed_content.get('paths', {})
            if not isinstance(paths, dict):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证 OpenAPI 内容失败: {e}")
            return False
    
    def parse_specification(self, content: Dict[str, Any], spec_id: str = None, name: str = None) -> OpenAPISpecification:
        """解析 OpenAPI 规范"""
        try:
            if not spec_id:
                spec_id = str(uuid.uuid4())
            
            if not name:
                info = content.get('info', {})
                name = info.get('title', 'Untitled API')
            
            # 创建 OpenAPI 规范实例
            spec = OpenAPISpecification(spec_id, name, content)
            
            # 验证规范
            if not spec.validate():
                raise ValueError("OpenAPI 规范验证失败")
            
            self.logger.info(f"成功解析 OpenAPI 规范: {name}")
            return spec
            
        except Exception as e:
            self.logger.error(f"解析 OpenAPI 规范失败: {e}")
            raise
    
    def parse_endpoints(self, spec: OpenAPISpecification) -> List[Dict[str, Any]]:
        """解析端点信息"""
        endpoints = []
        paths = spec.get_paths()
        
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
                    
                    # 解析请求和响应模式
                    request_schema = self._parse_request_schema(operation, spec)
                    response_schema = self._parse_response_schema(operation, spec)
                    
                    # 解析安全配置
                    security = self._parse_security(operation, spec)
                    
                    endpoint = {
                        'id': str(uuid.uuid4()),
                        'endpoint_name': path,
                        'endpoint_type': 'http',
                        'method': method.upper(),
                        'operation_type': method.lower(),
                        'description': operation.get('summary', ''),
                        'parameters': all_params,
                        'request_schema': request_schema,
                        'response_schema': response_schema,
                        'security': security,
                        'status': 'active',
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    endpoints.append(endpoint)
        
        self.logger.info(f"解析了 {len(endpoints)} 个端点")
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
    
    def _parse_request_schema(self, operation: Dict[str, Any], spec: OpenAPISpecification) -> Dict[str, Any]:
        """解析请求模式"""
        request_body = operation.get('requestBody', {})
        if not request_body:
            return {}
        
        content = request_body.get('content', {})
        schemas = {}
        
        for content_type, content_info in content.items():
            schema = content_info.get('schema', {})
            if schema:
                # 解析引用
                if '$ref' in schema:
                    resolved_schema = spec.resolve_reference(schema['$ref'])
                    if resolved_schema:
                        schemas[content_type] = resolved_schema
                else:
                    schemas[content_type] = schema
        
        return {
            'required': request_body.get('required', False),
            'description': request_body.get('description', ''),
            'content': schemas
        }
    
    def _parse_response_schema(self, operation: Dict[str, Any], spec: OpenAPISpecification) -> Dict[str, Any]:
        """解析响应模式"""
        responses = operation.get('responses', {})
        schemas = {}
        
        for status_code, response in responses.items():
            content = response.get('content', {})
            response_schemas = {}
            
            for content_type, content_info in content.items():
                schema = content_info.get('schema', {})
                if schema:
                    # 解析引用
                    if '$ref' in schema:
                        resolved_schema = spec.resolve_reference(schema['$ref'])
                        if resolved_schema:
                            response_schemas[content_type] = resolved_schema
                    else:
                        response_schemas[content_type] = schema
            
            schemas[status_code] = {
                'description': response.get('description', ''),
                'content': response_schemas
            }
        
        return schemas
    
    def _parse_security(self, operation: Dict[str, Any], spec: OpenAPISpecification) -> List[Dict[str, Any]]:
        """解析安全配置"""
        # 获取操作级别的安全配置，如果没有则使用全局配置
        security = operation.get('security', spec.get_global_security())
        
        # 解析安全方案
        security_schemes = spec.get_security_schemes()
        parsed_security = []
        
        for sec_item in security:
            for scheme_name, scopes in sec_item.items():
                scheme_def = security_schemes.get(scheme_name, {})
                parsed_security.append({
                    'name': scheme_name,
                    'type': scheme_def.get('type', ''),
                    'description': scheme_def.get('description', ''),
                    'scopes': scopes if isinstance(scopes, list) else []
                })
        
        return parsed_security
    
    def parse_components(self, spec: OpenAPISpecification) -> Dict[str, Any]:
        """解析组件信息"""
        components = spec.get_components()
        
        parsed_components = {
            'schemas': {},
            'securitySchemes': {},
            'parameters': {},
            'responses': {},
            'requestBodies': {},
            'headers': {},
            'examples': {},
            'links': {},
            'callbacks': {}
        }
        
        for component_type, component_items in components.items():
            if component_type in parsed_components:
                for name, definition in component_items.items():
                    # 解析引用
                    if isinstance(definition, dict) and '$ref' in definition:
                        resolved = spec.resolve_reference(definition['$ref'])
                        if resolved:
                            parsed_components[component_type][name] = resolved
                    else:
                        parsed_components[component_type][name] = definition
        
        return parsed_components
    
    def extract_parameters(self, operation: Dict[str, Any], spec: OpenAPISpecification) -> Dict[str, Any]:
        """提取参数信息"""
        parameters = operation.get('parameters', [])
        extracted = {
            'path': [],
            'query': [],
            'header': [],
            'cookie': []
        }
        
        for param in parameters:
            param_in = param.get('in', 'query')
            if param_in in extracted:
                extracted[param_in].append({
                    'name': param.get('name', ''),
                    'required': param.get('required', False),
                    'description': param.get('description', ''),
                    'schema': param.get('schema', {}),
                    'example': param.get('example'),
                    'deprecated': param.get('deprecated', False)
                })
        
        return extracted
    
    def validate_parameters(self, operation: Dict[str, Any], 
                          provided_params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证提供的参数"""
        errors = []
        parameters = operation.get('parameters', [])
        
        for param in parameters:
            param_name = param.get('name', '')
            param_in = param.get('in', 'query')
            required = param.get('required', False)
            
            # 检查必需参数
            if required and param_name not in provided_params:
                errors.append(f"缺少必需参数: {param_name}")
                continue
            
            # 如果参数存在，进行类型验证
            if param_name in provided_params:
                value = provided_params[param_name]
                schema = param.get('schema', {})
                
                # 简单的类型验证
                param_type = schema.get('type', 'string')
                if param_type == 'integer' and not isinstance(value, int):
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        errors.append(f"参数 {param_name} 必须是整数")
                elif param_type == 'number' and not isinstance(value, (int, float)):
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"参数 {param_name} 必须是数字")
                elif param_type == 'boolean' and not isinstance(value, bool):
                    if str(value).lower() not in ['true', 'false', '1', '0']:
                        errors.append(f"参数 {param_name} 必须是布尔值")
        
        return len(errors) == 0, errors 