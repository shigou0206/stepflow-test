"""
API 管理模块
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

from ..database.manager import DatabaseManager
from ..auth.manager import AuthManager
from .parser import OpenApiRefResolver, resolve_openapi_document, extract_endpoints_from_document


class ApiManager:
    """API管理器"""
    
    def __init__(self, db_manager: DatabaseManager, auth_manager: AuthManager):
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        self.ref_resolver = OpenApiRefResolver()
    
    # OpenAPI 文档解析和管理
    def register_api(self, name: str, openapi_content: str, version: str = None, base_url: str = None) -> Dict[str, Any]:
        """注册 OpenAPI 文档"""
        try:
            # 解析 OpenAPI 文档（处理 $ref 引用）
            self.logger.info(f"开始解析 OpenAPI 文档: {name}")
            resolved_doc = self.ref_resolver.resolve_document(openapi_content)
            self.logger.info(f"OpenAPI 文档解析完成: {name}")
            
            # 验证 OpenAPI 格式
            self._validate_openapi(resolved_doc)
            
            # 保存模板
            template_id = self._save_template(name, openapi_content)
            
            # 保存文档
            document_id = self._save_document(template_id, name, version, base_url, resolved_doc)
            
            # 提取并保存端点
            endpoints = self._extract_and_save_endpoints(resolved_doc, document_id)
            
            self.logger.info(f"API注册成功: {name} (ID: {document_id})")
            
            return {
                'success': True,
                'template_id': template_id,
                'document_id': document_id,
                'endpoints': endpoints
            }
            
        except Exception as e:
            self.logger.error(f"API注册失败: {name} - {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_openapi(self, doc: Dict[str, Any]):
        """验证 OpenAPI 文档格式"""
        if 'openapi' not in doc:
            raise ValueError("Missing 'openapi' field")
        
        if 'info' not in doc:
            raise ValueError("Missing 'info' field")
        
        if 'paths' not in doc:
            raise ValueError("Missing 'paths' field")
        
        # 验证 OpenAPI 版本
        openapi_version = doc['openapi']
        if not openapi_version.startswith('3.'):
            raise ValueError(f"Unsupported OpenAPI version: {openapi_version}")
    
    def _save_template(self, name: str, openapi_content: str) -> str:
        """保存 OpenAPI 模板"""
        template_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO openapi_templates 
                (id, name, content, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (template_id, name, openapi_content, 'active', now, now))
        
        return template_id
    
    def _save_document(self, template_id: str, name: str, version: str, base_url: str, resolved_doc: Dict[str, Any]) -> str:
        """保存 API 文档"""
        document_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 从解析后的文档中获取信息
        info = resolved_doc.get('info', {})
        doc_name = name or info.get('title', 'Unknown API')
        doc_version = version or info.get('version', '1.0.0')
        
        # 获取服务器信息
        servers = resolved_doc.get('servers', [])
        if servers and not base_url:
            base_url = servers[0].get('url', '')
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO api_documents 
                (id, template_id, name, version, base_url, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (document_id, template_id, doc_name, doc_version, base_url, 'active', now, now))
        
        return document_id
    
    def _extract_and_save_endpoints(self, resolved_doc: Dict[str, Any], document_id: str) -> List[Dict[str, Any]]:
        """提取并保存端点信息"""
        endpoints = self.ref_resolver.extract_endpoints(resolved_doc)
        saved_endpoints = []
        
        for endpoint in endpoints:
            endpoint_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # 保存端点
            with self.db_manager.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO api_endpoints 
                    (id, api_document_id, path, method, operation_id, summary, description, 
                     tags, status, call_count, success_count, error_count, avg_response_time_ms, 
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    endpoint_id,
                    document_id,
                    endpoint['path'],
                    endpoint['method'],
                    endpoint['operation_id'],
                    endpoint['summary'],
                    endpoint['description'],
                    json.dumps(endpoint['tags']) if endpoint['tags'] else None,
                    'active',
                    0, 0, 0, None,
                    now, now
                ))
            
            saved_endpoints.append({
                'id': endpoint_id,
                'path': endpoint['path'],
                'method': endpoint['method'],
                'operation_id': endpoint['operation_id'],
                'summary': endpoint['summary']
            })
        
        return saved_endpoints
    
    def get_api(self, api_id: str) -> Optional[Dict[str, Any]]:
        """获取 API 信息"""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                SELECT d.*, t.name as template_name, t.content as openapi_content
                FROM api_documents d
                JOIN openapi_templates t ON d.template_id = t.id
                WHERE d.id = ?
            ''', (api_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def list_apis(self, status: str = 'active') -> List[Dict[str, Any]]:
        """列出所有 API"""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                SELECT d.*, t.name as template_name
                FROM api_documents d
                JOIN openapi_templates t ON d.template_id = t.id
                WHERE d.status = ?
                ORDER BY d.created_at DESC
            ''', (status,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_api(self, api_id: str) -> bool:
        """删除 API"""
        try:
            with self.db_manager.get_cursor() as cursor:
                # 删除端点
                cursor.execute('DELETE FROM api_endpoints WHERE api_document_id = ?', (api_id,))
                
                # 删除文档
                cursor.execute('DELETE FROM api_documents WHERE id = ?', (api_id,))
                
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"删除 API 失败: {api_id} - {e}")
            return False
    
    def get_endpoint(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取端点信息"""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                SELECT e.*, d.name as api_name, d.base_url
                FROM api_endpoints e
                JOIN api_documents d ON e.api_document_id = d.id
                WHERE e.id = ?
            ''', (endpoint_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def list_endpoints(self, api_document_id: str = None) -> List[Dict[str, Any]]:
        """列出端点"""
        with self.db_manager.get_cursor() as cursor:
            if api_document_id:
                cursor.execute('''
                    SELECT e.*, d.name as api_name, d.base_url
                    FROM api_endpoints e
                    JOIN api_documents d ON e.api_document_id = d.id
                    WHERE e.api_document_id = ?
                    ORDER BY e.path, e.method
                ''', (api_document_id,))
            else:
                cursor.execute('''
                    SELECT e.*, d.name as api_name, d.base_url
                    FROM api_endpoints e
                    JOIN api_documents d ON e.api_document_id = d.id
                    ORDER BY e.path, e.method
                ''')
            
            endpoints = [dict(row) for row in cursor.fetchall()]
            
            # 为每个端点添加详细信息
            detailed_endpoints = []
            for endpoint in endpoints:
                detailed_endpoint = dict(endpoint)
                
                # 解析 tags
                try:
                    tags = json.loads(endpoint.get('tags', '[]'))
                    detailed_endpoint['tags'] = tags
                except:
                    detailed_endpoint['tags'] = []
                
                # 从 OpenAPI 文档中获取参数和 security 信息
                api_doc = self.get_api(endpoint['api_document_id'])
                if api_doc and api_doc.get('openapi_content'):
                    try:
                        openapi_doc = json.loads(api_doc['openapi_content'])
                        path_info = openapi_doc.get('paths', {}).get(endpoint['path'], {})
                        operation_info = path_info.get(endpoint['method'].lower(), {})
                        
                        # 获取参数信息
                        parameters = operation_info.get('parameters', [])
                        detailed_endpoint['parameters'] = parameters
                        
                        # 获取 security 信息
                        security = operation_info.get('security', [])
                        detailed_endpoint['security'] = security
                        
                        # 获取 requestBody 信息
                        request_body = operation_info.get('requestBody', {})
                        detailed_endpoint['request_body'] = request_body
                        
                        # 获取 responses 信息
                        responses = operation_info.get('responses', {})
                        detailed_endpoint['responses'] = responses
                        
                    except Exception as e:
                        self.logger.warning(f"解析端点详细信息失败: {endpoint['id']} - {e}")
                        detailed_endpoint['parameters'] = []
                        detailed_endpoint['security'] = []
                        detailed_endpoint['request_body'] = {}
                        detailed_endpoint['responses'] = {}
                else:
                    detailed_endpoint['parameters'] = []
                    detailed_endpoint['security'] = []
                    detailed_endpoint['request_body'] = {}
                    detailed_endpoint['responses'] = {}
                
                detailed_endpoints.append(detailed_endpoint)
            
            return detailed_endpoints
    
    def call_api_by_path(self, path: str, method: str, request_data: Dict[str, Any], api_document_id: str = None) -> Dict[str, Any]:
        """通过路径调用 API"""
        try:
            # 查找端点
            endpoints = self.list_endpoints(api_document_id)
            
            # 匹配路径和方法
            matched_endpoint = None
            
            # 首先尝试直接匹配（Flutter 端传递实际路径值，如 /pet/1）
            for endpoint in endpoints:
                if self._match_path(endpoint['path'], path) and endpoint['method'] == method.upper():
                    matched_endpoint = endpoint
                    break
            
            # 如果没有找到匹配，尝试匹配包含占位符的路径（Flutter 端传递 /pet/{petId}）
            if not matched_endpoint:
                for endpoint in endpoints:
                    if endpoint['path'] == path and endpoint['method'] == method.upper():
                        matched_endpoint = endpoint
                        break
            
            if not matched_endpoint:
                return {
                    'success': False,
                    'error': f'Endpoint not found: {method} {path}'
                }
            
            # 调用 API
            return self.call_api(matched_endpoint['id'], request_data)
            
        except Exception as e:
            self.logger.error(f"通过路径调用 API 失败: {method} {path} - {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _match_path(self, pattern: str, actual: str) -> bool:
        """匹配路径模式"""
        # 简单的路径匹配，支持参数
        # 例如: /users/{userId} 匹配 /users/123
        import re
        
        # 将 OpenAPI 路径参数转换为正则表达式
        regex_pattern = re.sub(r'\{[^}]+\}', r'[^/]+', pattern)
        regex_pattern = f"^{regex_pattern}$"
        
        return re.match(regex_pattern, actual) is not None
    
    # API 调用处理
    def call_api(self, endpoint_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用 API"""
        start_time = time.time()
        
        try:
            # 获取端点信息
            endpoint = self.get_endpoint(endpoint_id)
            if not endpoint:
                return {'success': False, 'error': 'Endpoint not found'}
            
            # 构建请求数据
            api_request = self.build_api_request(endpoint, request_data)
            
            # 执行 API 调用
            response = self.execute_api_call(api_request)
            
            # 计算响应时间
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 记录调用日志
            self.log_api_call(endpoint_id, api_request, response, response_time_ms)
            
            # 确保 response 带 success 字段
            if 'success' not in response:
                response['success'] = True
            response['response_time_ms'] = response_time_ms
            return response
            
        except Exception as e:
            self.logger.error(f"API调用失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def build_api_request(self, endpoint: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建 API 请求"""
        # 获取 API 文档信息
        api_doc = self.get_api(endpoint['api_document_id'])
        
        # 路径参数替换
        path = endpoint['path']
        params = dict(request_data.get('params', {})) if request_data.get('params') else {}
        path_params = dict(request_data.get('path_params', {})) if request_data.get('path_params') else {}
        
        import re
        def replace_path_param(match):
            key = match.group(1)
            # 优先从 path_params 中获取，然后从 params 中获取
            value = path_params.get(key) or params.get(key)
            if value is not None:
                # 替换后从 params 中移除（如果存在）
                if key in params:
                    params.pop(key)
                return str(value)
            return match.group(0)
        path = re.sub(r'\{([^}]+)\}', replace_path_param, path)
        
        # 构建完整 URL
        base_url = api_doc.get('base_url', '') if api_doc else ''
        # 确保路径参数被正确替换后，再拼接 URL
        if base_url and path:
            # 如果 base_url 不以 / 结尾，且 path 以 / 开头，则直接拼接
            if not base_url.endswith('/') and path.startswith('/'):
                full_url = base_url + path
            else:
                full_url = urljoin(base_url, path)
        else:
            full_url = base_url + path if base_url and path else (base_url or path)
        
        # 构建请求
        api_request = {
            'method': endpoint['method'],
            'url': full_url,
            'headers': request_data.get('headers', {}),
            'body': request_data.get('body'),
            'params': params,
            'client_ip': request_data.get('client_ip'),
            'user_agent': request_data.get('user_agent'),
            'api_document_id': endpoint['api_document_id'],
            'user_id': request_data.get('user_id')
        }
        
        # 设置默认头
        if 'Content-Type' not in api_request['headers']:
            api_request['headers']['Content-Type'] = 'application/json'
        
        if 'User-Agent' not in api_request['headers']:
            api_request['headers']['User-Agent'] = 'StepFlow-Gateway/1.0.0'
        
        # 应用认证配置
        self._apply_auth_config(api_request, endpoint['api_document_id'])
        
        return api_request
    
    def _apply_auth_config(self, api_request: Dict[str, Any], api_document_id: str):
        """应用认证配置"""
        try:
            # 获取该 API 文档的认证配置
            auth_configs = self.list_auth_configs(api_document_id=api_document_id)
            
            for auth_config in auth_configs:
                auth_type = auth_config.get('auth_type')
                auth_data = json.loads(auth_config.get('auth_config', '{}'))
                
                if auth_type == 'basic':
                    # Basic Auth
                    username = auth_data.get('username', '')
                    password = auth_data.get('password', '')
                    if username and password:
                        import base64
                        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                        api_request['headers']['Authorization'] = f"Basic {credentials}"
                
                elif auth_type == 'bearer':
                    # Bearer Token
                    token = auth_data.get('token', '')
                    if token:
                        api_request['headers']['Authorization'] = f"Bearer {token}"
                
                elif auth_type == 'api_key':
                    # API Key
                    key_in = auth_data.get('in', 'header')
                    key_name = auth_data.get('name', '')
                    key_value = auth_data.get('value', '')
                    
                    if key_name and key_value:
                        if key_in == 'header':
                            api_request['headers'][key_name] = key_value
                        elif key_in == 'query':
                            api_request['params'][key_name] = key_value
                        elif key_in == 'cookie':
                            # 处理 cookie
                            if 'Cookie' not in api_request['headers']:
                                api_request['headers']['Cookie'] = ''
                            api_request['headers']['Cookie'] += f"{key_name}={key_value}; "
                
                elif auth_type == 'oauth2':
                    # OAuth2 (简化处理，实际应该从缓存或数据库获取 token)
                    access_token = auth_data.get('access_token', '')
                    if access_token:
                        api_request['headers']['Authorization'] = f"Bearer {access_token}"
                
                # 只应用第一个配置（按优先级排序）
                break
                
        except Exception as e:
            self.logger.warning(f"应用认证配置失败: {e}")
    
    def execute_api_call(self, api_request: Dict[str, Any]) -> Dict[str, Any]:
        """执行 API 调用"""
        import requests
        
        method = api_request['method']
        url = api_request['url']
        headers = api_request['headers']
        body = api_request['body']
        params = api_request.get('params', {})
        
        try:
            # 发送实际的 HTTP 请求
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=body, params=params, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=body, params=params, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=body, params=params, timeout=30)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported HTTP method: {method}'
                }
            
            # 解析响应
            try:
                response_body = response.json() if response.content else {}
            except:
                response_body = response.text if response.content else {}
            
            return {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'response_body': response_body,
                'url': response.url
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP请求失败: {e}")
            return {
                'success': False,
                'error': f'HTTP request failed: {str(e)}',
                'status_code': 0
            }
        except Exception as e:
            self.logger.error(f"API调用异常: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 0
            }
    
    def log_api_call(self, endpoint_id: str, request: Dict[str, Any], 
                    response: Dict[str, Any], response_time_ms: int):
        """记录 API 调用日志"""
        log_id = str(uuid.uuid4())
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO api_call_logs 
                (id, api_endpoint_id, request_method, request_url, request_headers, 
                 request_body, request_params, response_status_code, response_headers, 
                 response_body, response_time_ms, client_ip, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id,
                endpoint_id,
                request['method'],
                request['url'],
                json.dumps(request['headers']),
                json.dumps(request['body']) if request['body'] else None,
                json.dumps(request['params']),
                response.get('status_code'),
                json.dumps(response.get('headers', {})),
                json.dumps(response.get('body', {})),
                response_time_ms,
                request.get('client_ip'),
                request.get('user_agent'),
                datetime.now().isoformat()
            ))
    
    # 认证配置管理
    def add_auth_config(self, api_document_id: str, auth_type: str, auth_config: Dict[str, Any],
                       is_required: bool = True, is_global: bool = False, priority: int = 0) -> str:
        """添加认证配置"""
        return self.db_manager.create_auth_config(
            api_document_id, auth_type, auth_config, is_required, is_global, priority
        )
    
    def get_auth_config(self, auth_config_id: str) -> Optional[Dict[str, Any]]:
        """获取认证配置"""
        return self.db_manager.get_auth_config(auth_config_id)
    
    def list_auth_configs(self, api_document_id: str = None, auth_type: str = None) -> List[Dict[str, Any]]:
        """列出认证配置"""
        return self.db_manager.list_auth_configs(api_document_id, auth_type)
    
    def update_auth_config(self, auth_config_id: str, auth_config: Dict[str, Any] = None,
                          is_required: bool = None, is_global: bool = None, priority: int = None) -> bool:
        """更新认证配置"""
        with self.db_manager.get_cursor() as cursor:
            updates = []
            params = []
            
            if auth_config is not None:
                updates.append("auth_config = ?")
                params.append(json.dumps(auth_config))
            
            if is_required is not None:
                updates.append("is_required = ?")
                params.append(is_required)
            
            if is_global is not None:
                updates.append("is_global = ?")
                params.append(is_global)
            
            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)
            
            if not updates:
                return False
            
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(auth_config_id)
            
            cursor.execute(f'''
                UPDATE api_auth_configs SET {', '.join(updates)} WHERE id = ?
            ''', params)
            
            return cursor.rowcount > 0
    
    def delete_auth_config(self, auth_config_id: str) -> bool:
        """删除认证配置"""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                UPDATE api_auth_configs SET status = 'deleted', updated_at = ? WHERE id = ?
            ''', (datetime.now().isoformat(), auth_config_id))
            
            return cursor.rowcount > 0
    
    # 资源引用管理
    def create_resource_reference(self, resource_type: str, resource_id: str, 
                                api_endpoint_id: str, display_name: str = None,
                                description: str = None, reference_config: Dict[str, Any] = None) -> str:
        """创建资源引用"""
        ref_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO resource_references 
                (id, resource_type, resource_id, api_endpoint_id, reference_config, 
                 display_name, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ref_id,
                resource_type,
                resource_id,
                api_endpoint_id,
                json.dumps(reference_config) if reference_config else None,
                display_name,
                description,
                'active',
                now,
                now
            ))
        
        self.logger.info(f"创建资源引用: {resource_type}:{resource_id} -> {api_endpoint_id}")
        return ref_id
    
    def get_resource_references(self, resource_type: str = None, resource_id: str = None) -> List[Dict[str, Any]]:
        """获取资源引用"""
        with self.db_manager.get_cursor() as cursor:
            query = "SELECT * FROM resource_references WHERE status = 'active'"
            params = []
            
            if resource_type:
                query += " AND resource_type = ?"
                params.append(resource_type)
            
            if resource_id:
                query += " AND resource_id = ?"
                params.append(resource_id)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('reference_config'):
                    result['reference_config'] = json.loads(result['reference_config'])
                results.append(result)
            
            return results
    
    # 统计和监控
    def get_api_statistics(self) -> Dict[str, Any]:
        """获取 API 统计信息"""
        return self.db_manager.get_statistics()
    
    def get_endpoint_statistics(self, endpoint_id: str) -> Dict[str, Any]:
        """获取端点统计信息"""
        return self.db_manager.get_endpoint_statistics(endpoint_id)
    
    def get_recent_api_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的 API 调用"""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                SELECT l.*, e.path, e.method, d.name as api_name
                FROM api_call_logs l
                JOIN api_endpoints e ON l.api_endpoint_id = e.id
                JOIN api_documents d ON e.api_document_id = d.id
                ORDER BY l.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_error_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取错误日志"""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                SELECT l.*, e.path, e.method, d.name as api_name
                FROM api_call_logs l
                JOIN api_endpoints e ON l.api_endpoint_id = e.id
                JOIN api_documents d ON e.api_document_id = d.id
                WHERE l.response_status_code >= 400 OR l.error_message IS NOT NULL
                ORDER BY l.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # 健康检查
    def check_api_health(self, api_document_id: str) -> Dict[str, Any]:
        """检查 API 健康状态"""
        try:
            # 获取 API 文档
            api_doc = self.db_manager.get_api_document(api_document_id)
            if not api_doc:
                return {'status': 'error', 'message': 'API document not found'}
            
            # 获取端点
            endpoints = self.list_endpoints(api_document_id)
            if not endpoints:
                return {'status': 'warning', 'message': 'No endpoints found'}
            
            # 检查端点状态
            active_endpoints = [ep for ep in endpoints if ep['status'] == 'active']
            
            # 记录健康检查
            check_id = str(uuid.uuid4())
            with self.db_manager.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO api_health_checks 
                    (id, api_document_id, check_type, status, details, checked_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    check_id,
                    api_document_id,
                    'endpoint_check',
                    'success' if active_endpoints else 'warning',
                    json.dumps({
                        'total_endpoints': len(endpoints),
                        'active_endpoints': len(active_endpoints),
                        'endpoint_details': [
                            {'path': ep['path'], 'method': ep['method'], 'status': ep['status']}
                            for ep in endpoints
                        ]
                    }),
                    datetime.now().isoformat()
                ))
            
            return {
                'status': 'success' if active_endpoints else 'warning',
                'api_name': api_doc['name'],
                'total_endpoints': len(endpoints),
                'active_endpoints': len(active_endpoints),
                'check_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"API健康检查失败: {e}")
            return {'status': 'error', 'message': str(e)} 