"""
Web 模型包
"""

from .user import UserRegisterRequest, UserLoginRequest
from .api import OpenApiRegisterRequest, ApiCallRequest
from .auth import AuthConfigRequest
from .common import SuccessResponse, ErrorResponse

__all__ = [
    'UserRegisterRequest',
    'UserLoginRequest', 
    'OpenApiRegisterRequest',
    'ApiCallRequest',
    'AuthConfigRequest',
    'SuccessResponse',
    'ErrorResponse'
] 