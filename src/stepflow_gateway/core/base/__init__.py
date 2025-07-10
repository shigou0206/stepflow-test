"""
StepFlow Gateway 核心基础模块

提供 API 网关的核心抽象类和基础功能。
"""

from .api_spec import ApiSpecification
from .parser import BaseParser
from .executor import BaseExecutor
from .protocol_adapter import BaseProtocolAdapter

__all__ = [
    "ApiSpecification",
    "BaseParser", 
    "BaseExecutor",
    "BaseProtocolAdapter"
] 