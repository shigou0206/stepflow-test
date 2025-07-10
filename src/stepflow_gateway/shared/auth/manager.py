"""
认证管理模块
"""

import hashlib
import hmac
import secrets
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..database.manager import DatabaseManager


@dataclass
class AuthResult:
    """认证结果"""
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    token: Optional[str] = None


class AuthManager:
    """认证管理器"""
    
    def __init__(self, database_manager: DatabaseManager, secret_key: str = None):
        self.db = database_manager
        self.logger = logging.getLogger(__name__)
        self.secret_key = secret_key or secrets.token_hex(32)
        self.token_expiry_hours = 24
    
    def hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """哈希密码"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # 使用 PBKDF2 进行密码哈希
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        )
        password_hash = hash_obj.hex()
        
        return password_hash, salt
    
    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """验证密码"""
        password_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(password_hash, stored_hash)
    
    def register_user(self, username: str, email: str, password: str, 
                     role: str = "user", permissions: Dict[str, Any] = None) -> AuthResult:
        """注册用户"""
        try:
            # 检查用户名是否已存在
            existing_user = self.db.get_user_by_username(username)
            if existing_user:
                return AuthResult(
                    success=False,
                    error_message="用户名已存在"
                )
            
            # 检查邮箱是否已存在
            existing_email = self.db.get_user_by_email(email)
            if existing_email:
                return AuthResult(
                    success=False,
                    error_message="邮箱已存在"
                )
            
            # 哈希密码
            password_hash, salt = self.hash_password(password)
            
            # 创建用户
            user_id = self.db.create_user(
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt,
                role=role,
                permissions=permissions
            )
            
            self.logger.info(f"用户注册成功: {username}")
            return AuthResult(
                success=True,
                user_id=user_id,
                username=username,
                role=role,
                permissions=permissions
            )
            
        except Exception as e:
            self.logger.error(f"用户注册失败: {e}")
            return AuthResult(
                success=False,
                error_message=f"注册失败: {str(e)}"
            )
    
    def login(self, username: str, password: str) -> AuthResult:
        """用户登录"""
        try:
            # 获取用户信息
            user = self.db.get_user_by_username(username)
            if not user:
                return AuthResult(
                    success=False,
                    error_message="用户名或密码错误"
                )
            
            # 验证密码
            if not self.verify_password(password, user['password_hash'], user['salt']):
                return AuthResult(
                    success=False,
                    error_message="用户名或密码错误"
                )
            
            # 生成 JWT token
            token = self.generate_token(user['id'], user['username'], user['role'])
            
            self.logger.info(f"用户登录成功: {username}")
            return AuthResult(
                success=True,
                user_id=user['id'],
                username=user['username'],
                role=user['role'],
                permissions=user.get('permissions'),
                token=token
            )
            
        except Exception as e:
            self.logger.error(f"用户登录失败: {e}")
            return AuthResult(
                success=False,
                error_message=f"登录失败: {str(e)}"
            )
    
    def generate_token(self, user_id: str, username: str, role: str) -> str:
        """生成 JWT token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> AuthResult:
        """验证 JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # 检查用户是否仍然存在且活跃
            user = self.db.get_user_by_username(payload['username'])
            if not user or not user.get('is_active'):
                return AuthResult(
                    success=False,
                    error_message="用户不存在或已被禁用"
                )
            
            return AuthResult(
                success=True,
                user_id=payload['user_id'],
                username=payload['username'],
                role=payload['role']
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(
                success=False,
                error_message="Token 已过期"
            )
        except jwt.InvalidTokenError:
            return AuthResult(
                success=False,
                error_message="无效的 Token"
            )
        except Exception as e:
            self.logger.error(f"Token 验证失败: {e}")
            return AuthResult(
                success=False,
                error_message="Token 验证失败"
            )
    
    def refresh_token(self, token: str) -> AuthResult:
        """刷新 Token"""
        # 验证当前 token
        auth_result = self.verify_token(token)
        if not auth_result.success:
            return auth_result
        
        # 生成新的 token
        new_token = self.generate_token(
            auth_result.user_id,
            auth_result.username,
            auth_result.role
        )
        
        return AuthResult(
            success=True,
            user_id=auth_result.user_id,
            username=auth_result.username,
            role=auth_result.role,
            permissions=auth_result.permissions,
            token=new_token
        )
    
    def logout(self, token: str) -> bool:
        """用户登出"""
        try:
            # 这里可以实现 token 黑名单机制
            # 目前只是记录日志
            auth_result = self.verify_token(token)
            if auth_result.success:
                self.logger.info(f"用户登出: {auth_result.username}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"用户登出失败: {e}")
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> AuthResult:
        """修改密码"""
        try:
            # 获取用户信息
            user = self.db.get_user_by_username(user_id)  # 假设 user_id 是用户名
            if not user:
                return AuthResult(
                    success=False,
                    error_message="用户不存在"
                )
            
            # 验证旧密码
            if not self.verify_password(old_password, user['password_hash'], user['salt']):
                return AuthResult(
                    success=False,
                    error_message="旧密码错误"
                )
            
            # 生成新密码哈希
            new_password_hash, new_salt = self.hash_password(new_password)
            
            # 更新数据库中的密码
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    UPDATE gateway_users 
                    SET password_hash = ?, salt = ?, updated_at = ?
                    WHERE id = ?
                ''', (new_password_hash, new_salt, datetime.now().isoformat(), user['id']))
            
            self.logger.info(f"密码修改成功: {user['username']}")
            return AuthResult(
                success=True,
                user_id=user['id'],
                username=user['username'],
                role=user['role']
            )
            
        except Exception as e:
            self.logger.error(f"密码修改失败: {e}")
            return AuthResult(
                success=False,
                error_message=f"密码修改失败: {str(e)}"
            )
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """检查用户是否有特定权限"""
        try:
            user = self.db.get_user_by_username(user_id)  # 假设 user_id 是用户名
            if not user:
                return False
            
            # 管理员拥有所有权限
            if user['role'] == 'admin':
                return True
            
            # 检查用户权限
            permissions = user.get('permissions', {})
            return permissions.get(permission, False)
            
        except Exception as e:
            self.logger.error(f"权限检查失败: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            return self.db.get_user_by_username(user_id)  # 假设 user_id 是用户名
        except Exception as e:
            self.logger.error(f"获取用户信息失败: {e}")
            return None 