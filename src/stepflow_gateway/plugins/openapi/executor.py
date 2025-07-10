"""
OpenAPI 执行器
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from ...core.base.executor import BaseExecutor
from .specification import OpenAPISpecification
from .protocols import HTTPProtocolAdapter


class OpenAPIExecutor(BaseExecutor):
    """OpenAPI 执行器实现"""
    
    def get_supported_protocols(self):
        return ["http", "https"]

    def __init__(self, protocol_adapter: HTTPProtocolAdapter = None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.protocol_adapter = protocol_adapter or HTTPProtocolAdapter()
    
    def execute(self, spec: OpenAPISpecification, operation: str, 
                params: Dict[str, Any] = None, data: Dict[str, Any] = None,
                headers: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行 OpenAPI 操作"""
        try:
            start_time = time.time()
            
            # 解析操作（格式：METHOD /path）
            if ' ' not in operation:
                raise ValueError("操作格式错误，应为 'METHOD /path'")
            
            method, path = operation.split(' ', 1)
            method = method.upper()
            
            # 获取操作定义
            operation_def = spec.get_operation(path, method.lower())
            if not operation_def:
                raise ValueError(f"未找到操作: {method} {path}")
            
            # 验证参数
            params = params or {}
            data = data or {}
            headers = headers or {}
            
            # 验证必需参数
            validation_result = self._validate_operation_params(operation_def, spec, params, data, headers)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': '参数验证失败',
                    'details': validation_result['errors']
                }
            
            # 构建请求
            request_data = self._build_request(spec, operation_def, path, method, params, data, headers)
            
            # 执行请求
            response = self.protocol_adapter.execute(request_data)
            
            # 计算响应时间
            response_time = int((time.time() - start_time) * 1000)
            
            # 记录日志
            self._log_api_call(spec, operation_def, request_data, response, response_time)
            
            return {
                'success': True,
                'response': response,
                'response_time_ms': response_time,
                'operation': operation,
                'spec_name': spec.name
            }
            
        except Exception as e:
            self.logger.error(f"执行 OpenAPI 操作失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'operation': operation,
                'spec_name': spec.name if spec else 'Unknown'
            }
    
    def _validate_operation_params(self, operation_def: Dict[str, Any], spec: OpenAPISpecification,
                                 params: Dict[str, Any], data: Dict[str, Any], 
                                 headers: Dict[str, Any]) -> Dict[str, Any]:
        """验证操作参数"""
        errors = []
        parameters = operation_def.get('parameters', [])
        
        # 验证路径参数
        path_params = [p for p in parameters if p.get('in') == 'path']
        for param in path_params:
            param_name = param.get('name', '')
            required = param.get('required', False)
            
            if required and param_name not in params:
                errors.append(f"缺少必需路径参数: {param_name}")
            elif param_name in params:
                # 类型验证
                validation_error = self._validate_param_type(param, params[param_name])
                if validation_error:
                    errors.append(validation_error)
        
        # 验证查询参数
        query_params = [p for p in parameters if p.get('in') == 'query']
        for param in query_params:
            param_name = param.get('name', '')
            required = param.get('required', False)
            
            if required and param_name not in params:
                errors.append(f"缺少必需查询参数: {param_name}")
            elif param_name in params:
                validation_error = self._validate_param_type(param, params[param_name])
                if validation_error:
                    errors.append(validation_error)
        
        # 验证请求体
        request_body = operation_def.get('requestBody', {})
        if request_body and request_body.get('required', False) and not data:
            errors.append("缺少必需请求体")
        
        # 验证头部参数
        header_params = [p for p in parameters if p.get('in') == 'header']
        for param in header_params:
            param_name = param.get('name', '').lower()  # HTTP 头部不区分大小写
            required = param.get('required', False)
            
            if required and param_name not in [k.lower() for k in headers.keys()]:
                errors.append(f"缺少必需头部参数: {param_name}")
            elif param_name in [k.lower() for k in headers.keys()]:
                # 找到对应的头部值
                header_value = next((v for k, v in headers.items() if k.lower() == param_name), None)
                if header_value:
                    validation_error = self._validate_param_type(param, header_value)
                    if validation_error:
                        errors.append(validation_error)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_param_type(self, param: Dict[str, Any], value: Any) -> Optional[str]:
        """验证参数类型"""
        schema = param.get('schema', {})
        param_type = schema.get('type', 'string')
        param_name = param.get('name', '')
        
        try:
            if param_type == 'integer':
                int(value)
            elif param_type == 'number':
                float(value)
            elif param_type == 'boolean':
                if str(value).lower() not in ['true', 'false', '1', '0']:
                    return f"参数 {param_name} 必须是布尔值"
            elif param_type == 'array':
                if not isinstance(value, list):
                    return f"参数 {param_name} 必须是数组"
            elif param_type == 'object':
                if not isinstance(value, dict):
                    return f"参数 {param_name} 必须是对象"
        except (ValueError, TypeError):
            return f"参数 {param_name} 类型错误，期望 {param_type}"
        
        return None
    
    def _build_request(self, spec: OpenAPISpecification, operation_def: Dict[str, Any],
                      path: str, method: str, params: Dict[str, Any], 
                      data: Dict[str, Any], headers: Dict[str, Any]) -> Dict[str, Any]:
        """构建请求数据"""
        # 获取服务器配置
        servers = spec.get_servers()
        base_url = servers[0]['url'] if servers else 'http://localhost'
        
        # 替换路径参数
        processed_path = path
        path_params = [p for p in operation_def.get('parameters', []) if p.get('in') == 'path']
        for param in path_params:
            param_name = param.get('name', '')
            if param_name in params:
                processed_path = processed_path.replace(f'{{{param_name}}}', str(params[param_name]))
        
        # 构建查询参数
        query_params = {}
        query_param_defs = [p for p in operation_def.get('parameters', []) if p.get('in') == 'query']
        for param in query_param_defs:
            param_name = param.get('name', '')
            if param_name in params:
                query_params[param_name] = params[param_name]
        
        # 构建请求头
        request_headers = headers.copy()
        header_param_defs = [p for p in operation_def.get('parameters', []) if p.get('in') == 'header']
        for param in header_param_defs:
            param_name = param.get('name', '').lower()
            if param_name in [k.lower() for k in params.keys()]:
                header_value = next((v for k, v in params.items() if k.lower() == param_name), None)
                if header_value:
                    request_headers[param.get('name', '')] = header_value
        
        # 设置默认内容类型
        if method in ['POST', 'PUT', 'PATCH'] and data and 'content-type' not in [k.lower() for k in request_headers.keys()]:
            request_headers['Content-Type'] = 'application/json'
        
        # 构建请求数据
        request_data = {
            'method': method,
            'url': base_url + processed_path,
            'headers': request_headers,
            'params': query_params,
            'data': data if data else None,
            'timeout': 30,
            'verify': True
        }
        
        return request_data
    
    def _log_api_call(self, spec: OpenAPISpecification, operation_def: Dict[str, Any],
                     request_data: Dict[str, Any], response: Dict[str, Any], 
                     response_time: int):
        """记录 API 调用日志"""
        try:
            # 这里可以集成数据库管理器来记录日志
            self.logger.info(f"API 调用: {request_data['method']} {request_data['url']} "
                           f"- 响应时间: {response_time}ms - 状态: {response.get('status_code', 'Unknown')}")
        except Exception as e:
            self.logger.error(f"记录 API 调用日志失败: {e}")
    
    def list_operations(self, spec: OpenAPISpecification) -> List[Dict[str, Any]]:
        """列出所有可用操作"""
        operations = []
        paths = spec.get_paths()
        
        for path, path_item in paths.items():
            http_methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace']
            
            for method in http_methods:
                if method in path_item:
                    operation = path_item[method]
                    operations.append({
                        'operation': f"{method.upper()} {path}",
                        'summary': operation.get('summary', ''),
                        'description': operation.get('description', ''),
                        'method': method.upper(),
                        'path': path,
                        'parameters': operation.get('parameters', []),
                        'tags': operation.get('tags', [])
                    })
        
        return operations
    
    def get_operation_info(self, spec: OpenAPISpecification, operation: str) -> Optional[Dict[str, Any]]:
        """获取操作详细信息"""
        try:
            if ' ' not in operation:
                return None
            
            method, path = operation.split(' ', 1)
            method = method.upper()
            
            operation_def = spec.get_operation(path, method.lower())
            if not operation_def:
                return None
            
            return {
                'operation': operation,
                'summary': operation_def.get('summary', ''),
                'description': operation_def.get('description', ''),
                'method': method,
                'path': path,
                'parameters': operation_def.get('parameters', []),
                'requestBody': operation_def.get('requestBody', {}),
                'responses': operation_def.get('responses', {}),
                'security': operation_def.get('security', []),
                'tags': operation_def.get('tags', [])
            }
        except Exception as e:
            self.logger.error(f"获取操作信息失败: {e}")
            return None 