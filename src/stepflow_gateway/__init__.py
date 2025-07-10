"""
StepFlow Gateway - 动态API网关

一个集成到AI驱动平台的动态API网关，支持OpenAPI文档解析、
动态API调用、认证管理和OAuth2回调流程。
"""

__version__ = "1.0.0"
__author__ = "StepFlow Team"
__description__ = "Dynamic API Gateway for AI-driven platforms"

from .core.gateway import StepFlowGateway
from .core.config import GatewayConfig
from .database.manager import DatabaseManager
from .auth.manager import AuthManager
from .api.manager import ApiManager

__all__ = [
    "StepFlowGateway",
    "GatewayConfig", 
    "DatabaseManager",
    "AuthManager",
    "ApiManager"
] 