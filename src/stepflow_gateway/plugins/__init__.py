"""
StepFlow Gateway 插件模块

提供各种 API 规范的插件实现，包括 OpenAPI、AsyncAPI 等。
"""

__version__ = "1.0.0"

# 插件注册函数
def register_plugins(registry):
    """注册所有插件"""
    # 注册 OpenAPI 插件
    from .openapi import register_openapi_plugin
    register_openapi_plugin(registry)
    
    # 注册 AsyncAPI 插件
    from .asyncapi import register_asyncapi_plugin
    register_asyncapi_plugin(registry)

__all__ = ["register_plugins"] 