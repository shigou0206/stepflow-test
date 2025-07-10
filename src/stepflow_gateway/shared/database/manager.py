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

from ...core.config import DatabaseConfig


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
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def initialize(self):
        """初始化数据库"""
        # 尝试多个可能的模式文件位置
        schema_paths = [
            Path(__file__).parent.parent.parent.parent / "database" / "schema" / "stepflow_gateway.sql",
            Path(__file__).parent.parent.parent.parent.parent / "database" / "schema" / "stepflow_gateway.sql",
            Path(__file__).parent / "schema" / "stepflow_gateway.sql"
        ]
        
        schema_file = None
        for path in schema_paths:
            if path.exists():
                schema_file = path
                break
        
        if not schema_file:
            # 如果找不到模式文件，创建基本的表结构
            self._create_basic_schema()
            self.logger.info("使用基本数据库模式")
            return
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            self.connection.executescript(sql_content)
            self.connection.commit()
            self.logger.info("数据库初始化成功")
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _create_basic_schema(self):
        """创建基本的数据库模式"""
        sql_content = """
        -- API 规范模板表 (统一)
        CREATE TABLE IF NOT EXISTS api_spec_templates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            spec_type TEXT NOT NULL,  -- openapi, asyncapi, graphql, etc.
            content TEXT NOT NULL,
            version TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- API 文档表 (统一)
        CREATE TABLE IF NOT EXISTS api_documents (
            id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            name TEXT NOT NULL,
            spec_type TEXT NOT NULL,  -- openapi, asyncapi, graphql, etc.
            version TEXT,
            base_url TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (template_id) REFERENCES api_spec_templates(id)
        );

        -- 端点表 (统一，支持不同类型的端点)
        CREATE TABLE IF NOT EXISTS api_endpoints (
            id TEXT PRIMARY KEY,
            api_document_id TEXT NOT NULL,
            endpoint_name TEXT NOT NULL,  -- path for OpenAPI, channel for AsyncAPI
            endpoint_type TEXT NOT NULL,  -- http, mqtt, kafka, websocket, etc.
            method TEXT,                  -- HTTP method for REST APIs
            operation_type TEXT,          -- get, post, publish, subscribe, etc.
            description TEXT,
            parameters TEXT,              -- JSON
            request_schema TEXT,          -- JSON
            response_schema TEXT,         -- JSON
            security TEXT,                -- JSON
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (api_document_id) REFERENCES api_documents(id)
        );

        -- 协议配置表
        CREATE TABLE IF NOT EXISTS protocol_configs (
            id TEXT PRIMARY KEY,
            api_document_id TEXT NOT NULL,
            protocol_name TEXT NOT NULL,
            protocol_type TEXT NOT NULL,  -- http, mqtt, kafka, amqp, etc.
            config TEXT NOT NULL,         -- JSON
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (api_document_id) REFERENCES api_documents(id)
        );

        -- API 调用日志表 (统一)
        CREATE TABLE IF NOT EXISTS api_call_logs (
            id TEXT PRIMARY KEY,
            endpoint_id TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            request_data TEXT,            -- JSON
            response_data TEXT,           -- JSON
            protocol_type TEXT NOT NULL,
            status TEXT NOT NULL,         -- success/error
            error_message TEXT,
            response_time_ms INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id)
        );

        -- 用户表
        CREATE TABLE IF NOT EXISTS gateway_users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            permissions TEXT,             -- JSON
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- 会话表
        CREATE TABLE IF NOT EXISTS gateway_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            client_info TEXT,             -- JSON
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES gateway_users(id)
        );

        -- API 认证配置表
        CREATE TABLE IF NOT EXISTS api_auth_configs (
            id TEXT PRIMARY KEY,
            api_document_id TEXT NOT NULL,
            auth_type TEXT NOT NULL,      -- basic, bearer, api_key, oauth2
            config TEXT NOT NULL,         -- JSON
            priority INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (api_document_id) REFERENCES api_documents(id)
        );

        -- 认证凭据表
        CREATE TABLE IF NOT EXISTS auth_credentials (
            id TEXT PRIMARY KEY,
            auth_config_id TEXT NOT NULL,
            credential_type TEXT NOT NULL, -- username_password, token, api_key
            credential_data TEXT NOT NULL, -- JSON (encrypted)
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id)
        );

        -- 认证日志表
        CREATE TABLE IF NOT EXISTS auth_logs (
            id TEXT PRIMARY KEY,
            auth_config_id TEXT NOT NULL,
            user_id TEXT,
            auth_type TEXT NOT NULL,
            status TEXT NOT NULL,         -- success, failed
            error_message TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id),
            FOREIGN KEY (user_id) REFERENCES gateway_users(id)
        );
        """
        
        self.connection.executescript(sql_content)
        self.connection.commit()
    
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
    
    # 用户管理
    def create_user(self, username: str, email: str, password_hash: str, 
                   salt: str, role: str = "user", permissions: Dict[str, Any] = None) -> str:
        """创建用户"""
        user_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO gateway_users 
                (id, username, email, password_hash, salt, role, permissions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, username, email, password_hash, salt, role,
                json.dumps(permissions) if permissions else None,
                now, now
            ))
        
        self.logger.info(f"创建用户: {username}")
        return user_id
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """通过用户名获取用户"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM gateway_users WHERE username = ? AND is_active = 1
            ''', (username,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('permissions'):
                    result['permissions'] = json.loads(result['permissions'])
                return result
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """通过邮箱获取用户"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM gateway_users WHERE email = ? AND is_active = 1
            ''', (email,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('permissions'):
                    result['permissions'] = json.loads(result['permissions'])
                return result
            return None
    
    # API 文档管理
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
    
    def list_api_documents(self, spec_type: str = None, status: str = 'active') -> List[Dict[str, Any]]:
        """列出 API 文档"""
        with self.get_cursor() as cursor:
            if spec_type:
                cursor.execute('''
                    SELECT d.*, t.name as template_name
                    FROM api_documents d
                    JOIN api_spec_templates t ON d.template_id = t.id
                    WHERE d.spec_type = ? AND d.status = ? 
                    ORDER BY d.created_at DESC
                ''', (spec_type, status))
            else:
                cursor.execute('''
                    SELECT d.*, t.name as template_name
                    FROM api_documents d
                    JOIN api_spec_templates t ON d.template_id = t.id
                    WHERE d.status = ? 
                    ORDER BY d.created_at DESC
                ''', (status,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # 端点管理
    def get_endpoint(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取端点"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT e.*, d.spec_type 
                FROM api_endpoints e
                JOIN api_documents d ON e.api_document_id = d.id
                WHERE e.id = ?
            ''', (endpoint_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                # 解析 JSON 字段
                for field in ['parameters', 'request_schema', 'response_schema', 'security']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            result[field] = {}
                return result
            return None
    
    def list_endpoints(self, api_document_id: str = None, spec_type: str = None) -> List[Dict[str, Any]]:
        """列出端点"""
        with self.get_cursor() as cursor:
            if api_document_id:
                cursor.execute('''
                    SELECT e.*, d.spec_type 
                    FROM api_endpoints e
                    JOIN api_documents d ON e.api_document_id = d.id
                    WHERE e.api_document_id = ? AND e.status = 'active'
                    ORDER BY e.created_at DESC
                ''', (api_document_id,))
            elif spec_type:
                cursor.execute('''
                    SELECT e.*, d.spec_type 
                    FROM api_endpoints e
                    JOIN api_documents d ON e.api_document_id = d.id
                    WHERE d.spec_type = ? AND e.status = 'active'
                    ORDER BY e.created_at DESC
                ''', (spec_type,))
            else:
                cursor.execute('''
                    SELECT e.*, d.spec_type 
                    FROM api_endpoints e
                    JOIN api_documents d ON e.api_document_id = d.id
                    WHERE e.status = 'active'
                    ORDER BY e.created_at DESC
                ''')
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # 解析 JSON 字段
                for field in ['parameters', 'request_schema', 'response_schema', 'security']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            result[field] = {}
                results.append(result)
            
            return results
    
    # 认证配置管理
    def list_auth_configs(self, api_document_id: str = None) -> List[Dict[str, Any]]:
        """列出认证配置"""
        with self.get_cursor() as cursor:
            if api_document_id:
                cursor.execute('''
                    SELECT * FROM api_auth_configs 
                    WHERE api_document_id = ? AND is_active = 1
                    ORDER BY priority DESC
                ''', (api_document_id,))
            else:
                cursor.execute('''
                    SELECT * FROM api_auth_configs 
                    WHERE is_active = 1
                    ORDER BY priority DESC
                ''')
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('config'):
                    try:
                        result['config'] = json.loads(result['config'])
                    except:
                        result['config'] = {}
                results.append(result)
            
            return results
    
    # 日志管理
    def log_api_call(self, endpoint_id: str, operation_type: str, request_data: Dict[str, Any],
                    response_data: Dict[str, Any], protocol_type: str, status: str,
                    error_message: str = None, response_time_ms: int = 0):
        """记录 API 调用日志"""
        log_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO api_call_logs 
                (id, endpoint_id, operation_type, request_data, response_data, 
                 protocol_type, status, error_message, response_time_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id, endpoint_id, operation_type,
                json.dumps(request_data, ensure_ascii=False),
                json.dumps(response_data, ensure_ascii=False),
                protocol_type, status, error_message, response_time_ms, now
            ))
    
    def get_recent_api_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的 API 调用"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM api_call_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                for field in ['request_data', 'response_data']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            result[field] = {}
                results.append(result)
            
            return results
    
    def get_error_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取错误日志"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM api_call_logs 
                WHERE status = 'error'
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                for field in ['request_data', 'response_data']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            result[field] = {}
                results.append(result)
            
            return results 