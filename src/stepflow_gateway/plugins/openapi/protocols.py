"""
OpenAPI 协议适配器
"""

import json
import logging
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse

from ...core.base.protocol import BaseProtocolAdapter


class HTTPProtocolAdapter(BaseProtocolAdapter):
    """HTTP 协议适配器"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()

    @property
    def protocol_name(self):
        return "http"
    
    def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行 HTTP 请求"""
        try:
            method = request_data.get('method', 'GET').upper()
            url = request_data.get('url', '')
            headers = request_data.get('headers', {})
            params = request_data.get('params', {})
            data = request_data.get('data')
            timeout = request_data.get('timeout', 30)
            verify = request_data.get('verify', True)
            
            # 处理请求数据
            if data and isinstance(data, dict):
                # 检查内容类型
                content_type = headers.get('Content-Type', '').lower()
                if 'application/json' in content_type:
                    json_data = data
                    form_data = None
                else:
                    json_data = None
                    form_data = data
            else:
                json_data = None
                form_data = data
            
            # 执行请求
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                data=form_data,
                timeout=timeout,
                verify=verify
            )
            
            # 解析响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text
            
            result = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response_data,
                'url': response.url,
                'method': method,
                'success': response.status_code < 400
            }
            
            self.logger.info(f"HTTP 请求成功: {method} {url} - 状态码: {response.status_code}")
            return result
            
        except requests.exceptions.Timeout:
            self.logger.error(f"HTTP 请求超时: {method} {url}")
            return {
                'success': False,
                'error': '请求超时',
                'status_code': 408,
                'method': method,
                'url': url
            }
        except requests.exceptions.ConnectionError:
            self.logger.error(f"HTTP 连接错误: {method} {url}")
            return {
                'success': False,
                'error': '连接错误',
                'status_code': 503,
                'method': method,
                'url': url
            }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP 请求失败: {method} {url} - {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 500,
                'method': method,
                'url': url
            }
        except Exception as e:
            self.logger.error(f"HTTP 协议适配器错误: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 500,
                'method': method,
                'url': url
            }
    
    def build_url(self, base_url: str, path: str) -> str:
        """构建完整 URL"""
        try:
            # 如果路径是绝对路径，直接返回
            if path.startswith('http://') or path.startswith('https://'):
                return path
            
            # 处理基础 URL 和路径的拼接
            parsed_base = urlparse(base_url)
            
            # 如果基础 URL 已经有路径，需要正确处理拼接
            if parsed_base.path and not parsed_base.path.endswith('/'):
                # 基础 URL 有路径且不以 / 结尾，需要拼接
                if path.startswith('/'):
                    # 路径以 / 开头，替换基础 URL 的路径
                    return f"{parsed_base.scheme}://{parsed_base.netloc}{path}"
                else:
                    # 路径不以 / 开头，在基础 URL 路径后添加
                    return f"{parsed_base.scheme}://{parsed_base.netloc}{parsed_base.path}/{path}"
            else:
                # 基础 URL 没有路径或以 / 结尾，直接拼接
                return urljoin(base_url, path)
                
        except Exception as e:
            self.logger.error(f"URL 构建失败: {e}")
            return urljoin(base_url, path)
    
    def add_auth_headers(self, headers: Dict[str, Any], auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """添加认证头部"""
        auth_type = auth_config.get('type', '')
        updated_headers = headers.copy()
        
        if auth_type == 'apiKey':
            api_key = auth_config.get('api_key', '')
            name = auth_config.get('name', '')
            in_location = auth_config.get('in', 'header')
            
            if in_location == 'header':
                updated_headers[name] = api_key
            elif in_location == 'query':
                # 查询参数在请求时处理
                pass
        
        elif auth_type == 'bearer':
            token = auth_config.get('token', '')
            updated_headers['Authorization'] = f"Bearer {token}"
        
        elif auth_type == 'basic':
            username = auth_config.get('username', '')
            password = auth_config.get('password', '')
            import base64
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            updated_headers['Authorization'] = f"Basic {credentials}"
        
        return updated_headers
    
    def validate_response(self, response: Dict[str, Any], expected_schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """验证响应"""
        validation_result = {
            'valid': True,
            'errors': []
        }
        
        # 检查状态码
        status_code = response.get('status_code', 0)
        if status_code >= 400:
            validation_result['valid'] = False
            validation_result['errors'].append(f"HTTP 错误: {status_code}")
        
        # 如果有期望的模式，进行数据验证
        if expected_schema and response.get('data'):
            schema_errors = self._validate_against_schema(response['data'], expected_schema)
            validation_result['errors'].extend(schema_errors)
            if schema_errors:
                validation_result['valid'] = False
        
        return validation_result
    
    def _validate_against_schema(self, data: Any, schema: Dict[str, Any]) -> List[str]:
        """根据模式验证数据"""
        errors = []
        
        try:
            schema_type = schema.get('type', 'object')
            
            if schema_type == 'object':
                if not isinstance(data, dict):
                    errors.append("数据必须是对象")
                else:
                    # 检查必需字段
                    required_fields = schema.get('required', [])
                    for field in required_fields:
                        if field not in data:
                            errors.append(f"缺少必需字段: {field}")
                    
                    # 检查属性
                    properties = schema.get('properties', {})
                    for field_name, field_value in data.items():
                        if field_name in properties:
                            field_schema = properties[field_name]
                            field_errors = self._validate_against_schema(field_value, field_schema)
                            errors.extend([f"{field_name}.{error}" for error in field_errors])
            
            elif schema_type == 'array':
                if not isinstance(data, list):
                    errors.append("数据必须是数组")
                else:
                    items_schema = schema.get('items', {})
                    for i, item in enumerate(data):
                        item_errors = self._validate_against_schema(item, items_schema)
                        errors.extend([f"[{i}].{error}" for error in item_errors])
            
            elif schema_type == 'string':
                if not isinstance(data, str):
                    errors.append("数据必须是字符串")
                else:
                    # 检查格式
                    format_type = schema.get('format', '')
                    if format_type == 'email':
                        import re
                        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', data):
                            errors.append("必须是有效的邮箱格式")
                    elif format_type == 'uri':
                        if not data.startswith(('http://', 'https://', 'ftp://')):
                            errors.append("必须是有效的 URI 格式")
            
            elif schema_type == 'integer':
                if not isinstance(data, int):
                    try:
                        int(data)
                    except (ValueError, TypeError):
                        errors.append("数据必须是整数")
            
            elif schema_type == 'number':
                if not isinstance(data, (int, float)):
                    try:
                        float(data)
                    except (ValueError, TypeError):
                        errors.append("数据必须是数字")
            
            elif schema_type == 'boolean':
                if not isinstance(data, bool):
                    errors.append("数据必须是布尔值")
        
        except Exception as e:
            errors.append(f"模式验证错误: {e}")
        
        return errors
    
    def connect(self):
        """HTTP 协议无需显式连接"""
        pass

    def disconnect(self):
        """关闭 HTTP session"""
        if self.session:
            self.session.close() 