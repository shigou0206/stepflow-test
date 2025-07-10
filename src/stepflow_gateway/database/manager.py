"""
数据库管理模块
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime
import uuid

from ..core.config import DatabaseConfig


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._connection = None
    
    @property
    def connection(self):
        """获取数据库连接"""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.config.path,
                timeout=self.config.timeout,
                check_same_thread=self.config.check_same_thread,
                isolation_level=self.config.isolation_level
            )
            # 启用外键约束
            self._connection.execute("PRAGMA foreign_keys = ON")
            # 设置 WAL 模式以提高并发性能
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def initialize(self):
        """初始化数据库"""
        schema_file = Path(__file__).parent.parent.parent.parent / "database" / "schema" / "stepflow_gateway.sql"
        
        if not schema_file.exists():
            raise FileNotFoundError(f"数据库模式文件不存在: {schema_file}")
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            self.connection.executescript(sql_content)
            self.connection.commit()
            self.logger.info("数据库初始化成功")
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器"""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise
        finally:
            cursor.close()
    
    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    # OpenAPI 模板管理
    def create_template(self, name: str, content: str) -> str:
        """创建 OpenAPI 模板"""
        template_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO api_spec_templates (id, name, spec_type, content, version, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (template_id, name, 'openapi', content, '3.0.0', 'active', now, now))
        
        self.logger.info(f"创建模板: {name} (ID: {template_id})")
        return template_id
    
    def create_api_spec_template(self, name: str, content: str, spec_type: str = "openapi") -> str:
        """创建 API 规范模板（支持 OpenAPI 和 AsyncAPI）"""
        template_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 根据规范类型设置默认版本
        default_version = "3.0.0" if spec_type == "openapi" else "2.6.0"
        
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO api_spec_templates (id, name, spec_type, content, version, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (template_id, name, spec_type, content, default_version, 'active', now, now))
        
        self.logger.info(f"创建{spec_type}模板: {name} (ID: {template_id})")
        return template_id
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取模板"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM api_spec_templates WHERE id = ?
            ''', (template_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_templates(self, status: str = 'active') -> List[Dict[str, Any]]:
        """列出模板"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM api_spec_templates WHERE status = ? ORDER BY created_at DESC
            ''', (status,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_template(self, template_id: str, name: str = None, content: str = None) -> bool:
        """更新模板"""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(template_id)
        
        with self.get_cursor() as cursor:
            cursor.execute(f'''
                UPDATE api_spec_templates SET {', '.join(updates)} WHERE id = ?
            ''', params)
            
            return cursor.rowcount > 0
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                UPDATE api_spec_templates SET status = 'deleted', updated_at = ? WHERE id = ?
            ''', (datetime.now().isoformat(), template_id))
            
            return cursor.rowcount > 0
    
    # API 文档管理
    def create_api_document(self, template_id: str, name: str, version: str = None, 
                           base_url: str = None, spec_type: str = "openapi", status: str = "active") -> str:
        """创建 API 文档"""
        doc_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO api_documents (id, template_id, name, spec_type, version, base_url, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (doc_id, template_id, name, spec_type, version, base_url, status, now, now))
        
        self.logger.info(f"创建API文档: {name} (ID: {doc_id})")
        return doc_id
    
    def get_api_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取 API 文档"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT d.*, t.name as template_name, t.content as template_content
                FROM api_documents d
                JOIN api_spec_templates t ON d.template_id = t.id
                WHERE d.id = ?
            ''', (doc_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_api_documents(self, status: str = 'active') -> List[Dict[str, Any]]:
        """列出 API 文档"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT d.*, t.name as template_name
                FROM api_documents d
                JOIN api_spec_templates t ON d.template_id = t.id
                WHERE d.status = ? ORDER BY d.created_at DESC
            ''', (status,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # API 端点管理
    def create_endpoint(self, api_document_id: str, path: str, method: str, 
                       operation_id: str = None, summary: str = None, 
                       description: str = None, tags: List[str] = None) -> str:
        """创建 API 端点"""
        endpoint_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        tags_json = json.dumps(tags) if tags else None
        
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO api_endpoints 
                (id, api_document_id, path, method, operation_id, summary, description, tags, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (endpoint_id, api_document_id, path, method, operation_id, summary, 
                  description, tags_json, 'active', now, now))
        
        self.logger.info(f"创建端点: {method} {path} (ID: {endpoint_id})")
        return endpoint_id
    
    def create_api_endpoint(self, api_document_id: str, path: str, method: str, 
                           summary: str = None, description: str = None, 
                           parameters: List[Dict[str, Any]] = None,
                           request_body: Dict[str, Any] = None,
                           responses: Dict[str, Any] = None,
                           tags: List[str] = None, operation_id: str = None,
                           security: List[Dict[str, Any]] = None,
                           spec_type: str = "openapi",
                           operation_type: str = None,
                           protocol: str = None,
                           channel_name: str = None) -> str:
        """创建 API 端点（支持 AsyncAPI 字段）"""
        endpoint_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 处理 JSON 字段
        parameters_json = json.dumps(parameters) if parameters else None
        request_body_json = json.dumps(request_body) if request_body else None
        responses_json = json.dumps(responses) if responses else None
        tags_json = json.dumps(tags) if tags else None
        security_json = json.dumps(security) if security else None
        
        # 对于 AsyncAPI，使用 channel_name 作为 endpoint_name
        endpoint_name = channel_name if channel_name else path
        endpoint_type = protocol if protocol else "http"
        
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO api_endpoints 
                (id, api_document_id, endpoint_name, endpoint_type, method, operation_type,
                 description, parameters, request_schema, response_schema, security, 
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (endpoint_id, api_document_id, endpoint_name, endpoint_type, method, operation_type,
                  description, parameters_json, request_body_json, responses_json, security_json,
                  'active', now, now))
        
        self.logger.info(f"创建端点: {method} {endpoint_name} (ID: {endpoint_id})")
        return endpoint_id
    
    def get_endpoint(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取端点"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT e.*, d.name as api_name, d.base_url
                FROM api_endpoints e
                JOIN api_documents d ON e.api_document_id = d.id
                WHERE e.id = ?
            ''', (endpoint_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('tags'):
                    result['tags'] = json.loads(result['tags'])
                return result
            return None
    
    def list_endpoints(self, api_document_id: str = None, status: str = 'active') -> List[Dict[str, Any]]:
        """列出端点"""
        with self.get_cursor() as cursor:
            if api_document_id:
                cursor.execute('''
                    SELECT e.*, d.name as api_name, d.base_url
                    FROM api_endpoints e
                    JOIN api_documents d ON e.api_document_id = d.id
                    WHERE e.api_document_id = ? AND e.status = ?
                    ORDER BY e.path, e.method
                ''', (api_document_id, status))
            else:
                cursor.execute('''
                    SELECT e.*, d.name as api_name, d.base_url
                    FROM api_endpoints e
                    JOIN api_documents d ON e.api_document_id = d.id
                    WHERE e.status = ?
                    ORDER BY d.name, e.path, e.method
                ''', (status,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('tags'):
                    result['tags'] = json.loads(result['tags'])
                results.append(result)
            
            return results
    
    # 认证配置管理
    def create_auth_config(self, api_document_id: str, auth_type: str, auth_config: Dict[str, Any],
                          is_required: bool = True, is_global: bool = False, priority: int = 0) -> str:
        """创建认证配置"""
        auth_config_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO api_auth_configs 
                (id, api_document_id, auth_type, auth_config, is_required, is_global, priority, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (auth_config_id, api_document_id, auth_type, json.dumps(auth_config), 
                  is_required, is_global, priority, 'active', now, now))
        
        self.logger.info(f"创建认证配置: {auth_type} (ID: {auth_config_id})")
        return auth_config_id
    
    def get_auth_config(self, auth_config_id: str) -> Optional[Dict[str, Any]]:
        """获取认证配置"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM api_auth_configs WHERE id = ?
            ''', (auth_config_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['auth_config'] = json.loads(result['auth_config'])
                return result
            return None
    
    def list_auth_configs(self, api_document_id: str = None, auth_type: str = None) -> List[Dict[str, Any]]:
        """列出认证配置"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM api_auth_configs WHERE status = 'active'"
            params = []
            
            if api_document_id:
                query += " AND api_document_id = ?"
                params.append(api_document_id)
            
            if auth_type:
                query += " AND auth_type = ?"
                params.append(auth_type)
            
            query += " ORDER BY priority DESC, created_at DESC"
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['auth_config'] = json.loads(result['auth_config'])
                results.append(result)
            
            return results
    
    # 用户管理
    def create_user(self, username: str, email: str, password_hash: str, 
                   role: str = 'user', permissions: Dict[str, Any] = None, salt: str = None) -> str:
        """创建用户"""
        user_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        if salt is None:
            salt = str(uuid.uuid4())
        permissions_json = json.dumps(permissions) if permissions else None
        
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO gateway_users 
                (id, username, email, password_hash, salt, role, permissions, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, email, password_hash, salt, role, permissions_json, 1, now, now))
        
        self.logger.info(f"创建用户: {username} (ID: {user_id})")
        return user_id
    
    def get_user(self, user_id: str = None, username: str = None, email: str = None) -> Optional[Dict[str, Any]]:
        """获取用户"""
        with self.get_cursor() as cursor:
            if user_id:
                cursor.execute('SELECT * FROM gateway_users WHERE id = ?', (user_id,))
            elif username:
                cursor.execute('SELECT * FROM gateway_users WHERE username = ?', (username,))
            elif email:
                cursor.execute('SELECT * FROM gateway_users WHERE email = ?', (email,))
            else:
                return None
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('permissions'):
                    result['permissions'] = json.loads(result['permissions'])
                # 确保 salt 字段存在
                if 'salt' not in result:
                    result['salt'] = None
                return result
            return None
    
    def list_users(self, role: str = None, is_active: bool = True) -> List[Dict[str, Any]]:
        """列出用户"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM gateway_users WHERE is_active = ?"
            params = [is_active]
            
            if role:
                query += " AND role = ?"
                params.append(role)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('permissions'):
                    result['permissions'] = json.loads(result['permissions'])
                results.append(result)
            
            return results
    
    # 统计信息
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.get_cursor() as cursor:
            stats = {}
            
            # 模板统计
            cursor.execute('SELECT COUNT(*) as count FROM api_spec_templates WHERE status = "active"')
            stats['templates'] = cursor.fetchone()['count']
            
            # API文档统计
            cursor.execute('SELECT COUNT(*) as count FROM api_documents WHERE status = "active"')
            stats['api_documents'] = cursor.fetchone()['count']
            
            # 端点统计
            cursor.execute('SELECT COUNT(*) as count FROM api_endpoints WHERE status = "active"')
            stats['endpoints'] = cursor.fetchone()['count']
            
            # 用户统计
            cursor.execute('SELECT COUNT(*) as count FROM gateway_users WHERE is_active = 1')
            stats['users'] = cursor.fetchone()['count']
            
            # 认证配置统计
            cursor.execute('SELECT COUNT(*) as count FROM api_auth_configs WHERE status = "active"')
            stats['auth_configs'] = cursor.fetchone()['count']
            
            # API调用统计
            cursor.execute('SELECT COUNT(*) as count FROM api_call_logs')
            stats['api_calls'] = cursor.fetchone()['count']
            
            return stats
    
    def get_endpoint_statistics(self, endpoint_id: str) -> Dict[str, Any]:
        """获取端点统计信息"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT call_count, success_count, error_count, avg_response_time_ms
                FROM api_endpoints WHERE id = ?
            ''', (endpoint_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}
    
    def update_endpoint_stats(self, endpoint_id: str, response_status_code: int, response_time_ms: int):
        """更新端点统计信息"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                UPDATE api_endpoints 
                SET call_count = call_count + 1,
                    success_count = CASE WHEN ? BETWEEN 200 AND 299 THEN success_count + 1 ELSE success_count END,
                    error_count = CASE WHEN ? >= 400 THEN error_count + 1 ELSE error_count END,
                    avg_response_time_ms = CASE 
                        WHEN avg_response_time_ms IS NULL THEN ?
                        ELSE (avg_response_time_ms + ?) / 2
                    END,
                    updated_at = ?
                WHERE id = ?
            ''', (response_status_code, response_status_code, response_time_ms, 
                  response_time_ms, datetime.now().isoformat(), endpoint_id)) 