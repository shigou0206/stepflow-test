"""
认证管理模块
"""

import json
import logging
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import uuid

from ..core.config import AuthConfig, OAuth2Config
from ..database.manager import DatabaseManager


class AuthManager:
    """认证管理器"""
    
    def __init__(self, db_manager: DatabaseManager, auth_config: AuthConfig, oauth2_config: OAuth2Config):
        self.db_manager = db_manager
        self.auth_config = auth_config
        self.oauth2_config = oauth2_config
        self.logger = logging.getLogger(__name__)
    
    # 基础认证方法
    def authenticate_basic(self, username: str, password: str) -> Dict[str, Any]:
        """Basic认证"""
        try:
            # 获取用户
            user = self.db_manager.get_user(username=username)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # 验证密码
            if not self.verify_password(password, user['password_hash'], user['salt']):
                return {'success': False, 'error': 'Invalid password'}
            
            # 创建会话（写入数据库）
            session_token = self.create_session(user['id'])
            
            return {
                'success': True,
                'user': user,
                'session_token': session_token
            }
            
        except Exception as e:
            self.logger.error(f"Basic认证失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def authenticate_bearer(self, token: str) -> Dict[str, Any]:
        """Bearer Token认证"""
        try:
            # 验证会话令牌
            session = self.get_session_by_token(token)
            if not session:
                return {'success': False, 'error': 'Invalid token'}
            
            # 检查会话是否过期
            if datetime.fromisoformat(session['expires_at']) < datetime.now():
                return {'success': False, 'error': 'Token expired'}
            
            # 获取用户信息
            user = self.db_manager.get_user(user_id=session['user_id'])
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            return {
                'success': True,
                'user': user,
                'session': session
            }
            
        except Exception as e:
            self.logger.error(f"Bearer认证失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def authenticate_api_key(self, api_key: str) -> Dict[str, Any]:
        """API Key认证"""
        try:
            # 从缓存或数据库获取API Key信息
            # 这里简化处理，实际应该查询数据库
            return {
                'success': True,
                'api_key': api_key,
                'permissions': ['api_access']
            }
            
        except Exception as e:
            self.logger.error(f"API Key认证失败: {e}")
            return {'success': False, 'error': str(e)}
    
    # 密码管理
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """哈希密码"""
        if salt is None:
            salt = str(uuid.uuid4())
        
        # 使用bcrypt风格的哈希（简化实现）
        password_with_salt = password + salt
        password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
        
        return password_hash, salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """验证密码"""
        # 使用相同的哈希方法验证密码
        password_with_salt = password + salt
        expected_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
        return expected_hash == password_hash
    
    # 会话管理
    def create_session(self, user_id: str, client_info: Dict[str, Any] = None) -> str:
        """创建会话"""
        session_id = str(uuid.uuid4())
        session_token = self.generate_session_token(user_id)
        expires_at = datetime.now() + timedelta(minutes=self.auth_config.token_expire_minutes)
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO gateway_sessions 
                (id, user_id, session_token, expires_at, client_info, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                user_id,
                session_token,
                expires_at.isoformat(),
                json.dumps(client_info) if client_info else None,
                1,
                datetime.now().isoformat()
            ))
        
        self.logger.info(f"创建会话: {session_id} for user: {user_id}")
        return session_token
    
    def get_session_by_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """通过令牌获取会话"""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM gateway_sessions 
                WHERE session_token = ? AND is_active = 1
            ''', (session_token,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('client_info'):
                    result['client_info'] = json.loads(result['client_info'])
                return result
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """使会话失效"""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                UPDATE gateway_sessions 
                SET is_active = 0 WHERE session_token = ?
            ''', (session_token,))
            
            return cursor.rowcount > 0
    
    def generate_session_token(self, user_id: str) -> str:
        """生成会话令牌"""
        # 简化的令牌生成，实际应该使用JWT
        token_data = f"{user_id}:{datetime.now().isoformat()}:{secrets.token_hex(16)}"
        return base64.urlsafe_b64encode(token_data.encode()).decode()
    
    # API认证处理
    def handle_api_authentication(self, api_document_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理API认证"""
        try:
            # 获取API的认证配置
            auth_configs = self.db_manager.list_auth_configs(api_document_id=api_document_id)
            
            if not auth_configs:
                # 无需认证
                return {'success': True, 'auth_headers': {}}
            
            # 按优先级排序
            auth_configs.sort(key=lambda x: x['priority'], reverse=True)
            
            for auth_config in auth_configs:
                auth_result = self.execute_authentication(auth_config, request_data)
                if auth_result['success']:
                    return auth_result
            
            return {'success': False, 'error': 'All authentication methods failed'}
            
        except Exception as e:
            self.logger.error(f"API认证处理失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_authentication(self, auth_config: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行认证"""
        auth_type = auth_config['auth_type']
        config = auth_config['auth_config']
        
        try:
            if auth_type == 'basic':
                return self.execute_basic_auth(config, request_data)
            elif auth_type == 'bearer':
                return self.execute_bearer_auth(config, request_data)
            elif auth_type == 'api_key':
                return self.execute_api_key_auth(config, request_data)
            elif auth_type == 'oauth2':
                return self.execute_oauth2_auth(config, request_data)
            else:
                return {'success': False, 'error': f'Unsupported auth type: {auth_type}'}
                
        except Exception as e:
            self.logger.error(f"执行认证失败: {auth_type} - {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_basic_auth(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行Basic认证"""
        # 从请求头获取认证信息
        auth_header = request_data.get('headers', {}).get('Authorization', '')
        if not auth_header.startswith('Basic '):
            return {'success': False, 'error': 'Missing Basic auth header'}
        
        # 解析用户名密码
        try:
            credentials = base64.b64decode(auth_header[6:]).decode()
            username, password = credentials.split(':', 1)
        except Exception:
            return {'success': False, 'error': 'Invalid Basic auth format'}
        
        # 验证凭据
        auth_result = self.authenticate_basic(username, password)
        if not auth_result['success']:
            return auth_result
        
        # 记录认证日志
        self.log_auth_attempt(config['id'], 'basic', 'success', 'static', 50, request_data.get('client_ip'))
        
        return {
            'success': True,
            'auth_headers': {'Authorization': auth_header},
            'user': auth_result['user']
        }
    
    def execute_bearer_auth(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行Bearer认证"""
        # 从请求头获取token
        auth_header = request_data.get('headers', {}).get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {'success': False, 'error': 'Missing Bearer token'}
        
        token = auth_header[7:]
        
        # 验证token
        auth_result = self.authenticate_bearer(token)
        if not auth_result['success']:
            return auth_result
        
        # 记录认证日志
        self.log_auth_attempt(config['id'], 'bearer', 'success', 'static', 30, request_data.get('client_ip'))
        
        return {
            'success': True,
            'auth_headers': {'Authorization': auth_header},
            'user': auth_result['user']
        }
    
    def execute_api_key_auth(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行API Key认证"""
        key_name = config.get('key_name', 'X-API-Key')
        key_value = config.get('key_value')
        
        # 从请求头获取API Key
        api_key = request_data.get('headers', {}).get(key_name)
        if not api_key:
            return {'success': False, 'error': f'Missing {key_name}'}
        
        # 验证API Key
        if api_key != key_value:
            return {'success': False, 'error': 'Invalid API key'}
        
        # 记录认证日志
        self.log_auth_attempt(config['id'], 'api_key', 'success', 'static', 20, request_data.get('client_ip'))
        
        return {
            'success': True,
            'auth_headers': {key_name: api_key}
        }
    
    def execute_oauth2_auth(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行OAuth2认证"""
        # 检查是否有有效的用户授权
        user_id = request_data.get('user_id')
        if not user_id:
            return {'success': False, 'error': 'User not authenticated'}
        
        # 获取用户授权
        user_auth = self.get_user_authorization(user_id, request_data.get('api_document_id'))
        if not user_auth:
            return {'success': False, 'error': 'User not authorized for this API'}
        
        # 检查授权是否过期
        if user_auth.get('expires_at'):
            expires_at = datetime.fromisoformat(user_auth['expires_at'])
            if expires_at < datetime.now():
                return {'success': False, 'error': 'OAuth2 authorization expired'}
        
        # 记录认证日志
        self.log_auth_attempt(config['id'], 'oauth2', 'success', 'user_auth', 40, request_data.get('client_ip'))
        
        return {
            'success': True,
            'auth_headers': {
                'Authorization': f"Bearer {user_auth['access_token']}"
            },
            'user_auth': user_auth
        }
    
    # OAuth2 支持
    def create_oauth2_auth_state(self, user_id: str, api_document_id: str, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """创建OAuth2授权状态"""
        state_id = str(uuid.uuid4())
        state = secrets.token_urlsafe(16)
        
        # 生成PKCE参数
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        expires_at = datetime.now() + timedelta(minutes=self.oauth2_config.state_expire_minutes)
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO oauth2_auth_states 
                (id, auth_config_id, user_id, api_document_id, state, code_verifier, code_challenge, 
                 code_challenge_method, redirect_uri, scope, response_type, client_id, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                state_id,
                auth_config['id'],
                user_id,
                api_document_id,
                state,
                code_verifier,
                code_challenge,
                'S256',
                auth_config['auth_config']['redirect_uri'],
                auth_config['auth_config'].get('scope', self.oauth2_config.default_scope),
                'code',
                auth_config['auth_config']['client_id'],
                expires_at.isoformat(),
                datetime.now().isoformat()
            ))
        
        return {
            'id': state_id,
            'state': state,
            'code_verifier': code_verifier,
            'code_challenge': code_challenge,
            'expires_at': expires_at.isoformat()
        }
    
    def handle_oauth2_callback(self, auth_state_id: str, callback_code: str, callback_state: str) -> Dict[str, Any]:
        """处理OAuth2回调"""
        try:
            # 获取授权状态
            auth_state = self.get_oauth2_auth_state(auth_state_id)
            if not auth_state:
                return {'success': False, 'error': 'Invalid auth state'}
            
            # 验证state
            if auth_state['state'] != callback_state:
                return {'success': False, 'error': 'Invalid state parameter'}
            
            # 检查是否过期
            if datetime.fromisoformat(auth_state['expires_at']) < datetime.now():
                return {'success': False, 'error': 'Auth state expired'}
            
            # 模拟用授权码换取token
            token_response = self.exchange_code_for_token(callback_code, auth_state['code_verifier'])
            
            if token_response['success']:
                # 保存用户授权
                user_auth = self.save_user_authorization(
                    auth_state['user_id'],
                    auth_state['api_document_id'],
                    token_response
                )
                
                # 记录回调日志
                self.log_oauth2_callback(auth_state_id, auth_state['user_id'], 
                                       callback_code, callback_state, token_response)
                
                return {
                    'success': True,
                    'auth_id': token_response['auth_id'],
                    'user_auth': user_auth
                }
            else:
                return token_response
                
        except Exception as e:
            self.logger.error(f"OAuth2回调处理失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_oauth2_auth_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取OAuth2授权状态"""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM oauth2_auth_states WHERE id = ?
            ''', (state_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def exchange_code_for_token(self, auth_code: str, code_verifier: str) -> Dict[str, Any]:
        """用授权码换取token（模拟）"""
        # 实际实现中应该调用OAuth2提供商的token端点
        return {
            'success': True,
            'access_token': f"access_token_{secrets.token_hex(16)}",
            'refresh_token': f"refresh_token_{secrets.token_hex(16)}",
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'read profile',
            'auth_id': f"auth_user_{secrets.token_hex(8)}",
            'provider_user_id': f"provider_user_{secrets.token_hex(8)}"
        }
    
    def save_user_authorization(self, user_id: str, api_document_id: str, token_response: Dict[str, Any]) -> Dict[str, Any]:
        """保存用户授权"""
        auth_session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(seconds=token_response['expires_in'])
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO user_api_authorizations 
                (id, user_id, api_document_id, auth_config_id, access_token, refresh_token, 
                 token_type, expires_at, scope, auth_id, provider_user_id, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                auth_session_id,
                user_id,
                api_document_id,
                'oauth2-config-id',  # 实际应该从auth_state获取
                token_response['access_token'],
                token_response['refresh_token'],
                token_response['token_type'],
                expires_at.isoformat(),
                token_response['scope'],
                token_response['auth_id'],
                token_response['provider_user_id'],
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        return {
            'id': auth_session_id,
            'auth_id': token_response['auth_id'],
            'expires_at': expires_at.isoformat()
        }
    
    def get_user_authorization(self, user_id: str, api_document_id: str) -> Optional[Dict[str, Any]]:
        """获取用户授权"""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM user_api_authorizations 
                WHERE user_id = ? AND api_document_id = ? AND is_active = 1
            ''', (user_id, api_document_id))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # 日志记录
    def log_auth_attempt(self, auth_config_id: str, auth_type: str, auth_status: str, 
                        auth_method: str, response_time_ms: int, client_ip: str = None, 
                        error_message: str = None):
        """记录认证尝试"""
        log_id = str(uuid.uuid4())
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO auth_logs 
                (id, auth_config_id, auth_type, auth_status, auth_method, response_time_ms, 
                 client_ip, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id,
                auth_config_id,
                auth_type,
                auth_status,
                auth_method,
                response_time_ms,
                client_ip,
                error_message,
                datetime.now().isoformat()
            ))
    
    def log_oauth2_callback(self, auth_state_id: str, user_id: str, callback_code: str, 
                           callback_state: str, token_response: Dict[str, Any]):
        """记录OAuth2回调"""
        log_id = str(uuid.uuid4())
        
        with self.db_manager.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO oauth2_callback_logs 
                (id, auth_state_id, user_id, callback_code, callback_state, token_response, 
                 auth_id, provider_user_id, client_ip, callback_status, response_time_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id,
                auth_state_id,
                user_id,
                callback_code,
                callback_state,
                json.dumps(token_response),
                token_response['auth_id'],
                token_response['provider_user_id'],
                '192.168.1.102',  # 实际应该从请求获取
                'success',
                250,
                datetime.now().isoformat()
            )) 