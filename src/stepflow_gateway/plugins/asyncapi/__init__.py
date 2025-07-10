"""
AsyncAPI 插件
"""

from .specification import AsyncAPISpecification
from .parser import AsyncAPIParser
from .executor import AsyncAPIExecutor
from .protocol_adapter import AsyncAPIProtocolAdapter

__all__ = [
    'AsyncAPISpecification',
    'AsyncAPIParser', 
    'AsyncAPIExecutor',
    'AsyncAPIProtocolAdapter',
    'register_asyncapi_plugin'
]


def register_asyncapi_plugin(registry):
    """注册 AsyncAPI 插件"""
    # 注册规范
    registry.register_spec("asyncapi", AsyncAPISpecification)
    
    # 注册解析器
    registry.register_parser("asyncapi", AsyncAPIParser)
    
    # 注册执行器
    registry.register_executor("asyncapi", AsyncAPIExecutor)
    
    # 注册协议适配器
    registry.register_protocol("websocket", AsyncAPIProtocolAdapter)
    registry.register_protocol("mqtt", AsyncAPIProtocolAdapter)
    registry.register_protocol("amqp", AsyncAPIProtocolAdapter)
    registry.register_protocol("kafka", AsyncAPIProtocolAdapter)
    registry.register_protocol("nats", AsyncAPIProtocolAdapter) 