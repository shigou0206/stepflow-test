"""
用户相关模型
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"
    permissions: Optional[Dict[str, Any]] = None


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    permissions: Optional[Dict[str, Any]] = None


class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    token: Optional[str] = None
    error: Optional[str] = None 