"""
OpenAPI 插件模块
"""

from .specification import OpenAPISpecification
from .parser import OpenAPIParser
from .executor import OpenAPIExecutor
from .protocols import HTTPProtocolAdapter

__all__ = [
    "OpenAPISpecification",
    "OpenAPIParser", 
    "OpenAPIExecutor",
    "HTTPProtocolAdapter",
    "register_openapi_plugin"
]


def register_openapi_plugin(registry):
    """注册 OpenAPI 插件"""
    # 注册规范
    registry.register_spec("openapi", OpenAPISpecification)
    
    # 注册解析器
    registry.register_parser("openapi", OpenAPIParser)
    
    # 注册执行器
    registry.register_executor("openapi", OpenAPIExecutor)
    
    # 注册协议适配器
    registry.register_protocol("http", HTTPProtocolAdapter)
    registry.register_protocol("https", HTTPProtocolAdapter) 