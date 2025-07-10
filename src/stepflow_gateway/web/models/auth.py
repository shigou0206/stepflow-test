"""
认证相关模型
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class AuthConfigRequest(BaseModel):
    """认证配置请求"""
    api_document_id: str
    auth_type: str  # basic, bearer, api_key, oauth2
    auth_config: Dict[str, Any]
    is_required: bool = True
    is_global: bool = False
    priority: int = 0


class AuthConfigResponse(BaseModel):
    """认证配置响应"""
    id: str
    api_document_id: str
    auth_type: str
    auth_config: Dict[str, Any]
    auth_config_parsed: Optional[Dict[str, Any]] = None
    is_required: bool
    is_global: bool
    priority: int
    created_at: str
    updated_at: Optional[str] = None


class SessionRequest(BaseModel):
    """会话请求"""
    user_id: str
    client_info: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """会话响应"""
    success: bool
    session_token: Optional[str] = None
    error: Optional[str] = None


class SessionValidateRequest(BaseModel):
    """会话验证请求"""
    session_token: str


class OAuth2AuthUrlRequest(BaseModel):
    """OAuth2 认证 URL 请求"""
    user_id: str
    api_document_id: str


class OAuth2CallbackRequest(BaseModel):
    """OAuth2 回调请求"""
    auth_state_id: str
    callback_code: str
    callback_state: str 