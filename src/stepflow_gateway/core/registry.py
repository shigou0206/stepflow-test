"""
API 规范注册器
"""

import logging
from typing import Dict, Any, List, Optional, Type
from .base.api_spec import ApiSpecification
from .base.parser import BaseParser
from .base.executor import BaseExecutor
from .base.protocol import BaseProtocolAdapter


class ApiSpecRegistry:
    """API 规范注册器"""
    
    def __init__(self):
        self._specs = {}
        self._parsers = {}
        self._executors = {}
        self._protocols = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_spec(self, spec_type: str, spec_class: Type[ApiSpecification]):
        """注册 API 规范"""
        if not issubclass(spec_class, ApiSpecification):
            raise ValueError(f"Spec class must inherit from ApiSpecification: {spec_class}")
        
        self._specs[spec_type] = spec_class
        self.logger.info(f"Registered API specification: {spec_type}")
    
    def register_parser(self, spec_type: str, parser_class: Type[BaseParser]):
        """注册解析器"""
        if not issubclass(parser_class, BaseParser):
            raise ValueError(f"Parser class must inherit from BaseParser: {parser_class}")
        
        self._parsers[spec_type] = parser_class
        self.logger.info(f"Registered parser: {spec_type}")
    
    def register_executor(self, spec_type: str, executor_class: Type[BaseExecutor]):
        """注册执行器"""
        if not issubclass(executor_class, BaseExecutor):
            raise ValueError(f"Executor class must inherit from BaseExecutor: {executor_class}")
        
        self._executors[spec_type] = executor_class
        self.logger.info(f"Registered executor: {spec_type}")
    
    def register_protocol(self, protocol_name: str, protocol_class: Type[BaseProtocolAdapter]):
        """注册协议适配器"""
        if not issubclass(protocol_class, BaseProtocolAdapter):
            raise ValueError(f"Protocol class must inherit from BaseProtocolAdapter: {protocol_class}")
        
        self._protocols[protocol_name] = protocol_class
        self.logger.info(f"Registered protocol adapter: {protocol_name}")
    
    def get_spec(self, spec_type: str) -> Optional[Type[ApiSpecification]]:
        """获取规范类"""
        return self._specs.get(spec_type)
    
    def get_parser(self, spec_type: str) -> Optional[Type[BaseParser]]:
        """获取解析器类"""
        return self._parsers.get(spec_type)
    
    def get_executor(self, spec_type: str) -> Optional[Type[BaseExecutor]]:
        """获取执行器类"""
        return self._executors.get(spec_type)
    
    def get_protocol(self, protocol_name: str) -> Optional[Type[BaseProtocolAdapter]]:
        """获取协议适配器类"""
        return self._protocols.get(protocol_name)
    
    def create_spec(self, spec_type: str) -> Optional[ApiSpecification]:
        """创建规范实例"""
        spec_class = self.get_spec(spec_type)
        if spec_class:
            return spec_class()
        return None
    
    def create_parser(self, spec_type: str) -> Optional[BaseParser]:
        """创建解析器实例"""
        parser_class = self.get_parser(spec_type)
        if parser_class:
            return parser_class()
        return None
    
    def create_executor(self, spec_type: str, db_manager=None, auth_manager=None) -> Optional[BaseExecutor]:
        """创建执行器实例"""
        executor_class = self.get_executor(spec_type)
        if executor_class:
            return executor_class(db_manager, auth_manager)
        return None
    
    def create_protocol(self, protocol_name: str, config: Dict[str, Any]) -> Optional[BaseProtocolAdapter]:
        """创建协议适配器实例"""
        protocol_class = self.get_protocol(protocol_name)
        if protocol_class:
            return protocol_class(config)
        return None
    
    def list_specs(self) -> List[str]:
        """列出所有注册的规范类型"""
        return list(self._specs.keys())
    
    def list_parsers(self) -> List[str]:
        """列出所有注册的解析器类型"""
        return list(self._parsers.keys())
    
    def list_executors(self) -> List[str]:
        """列出所有注册的执行器类型"""
        return list(self._executors.keys())
    
    def list_protocols(self) -> List[str]:
        """列出所有注册的协议类型"""
        return list(self._protocols.keys())
    
    def get_spec_info(self, spec_type: str) -> Dict[str, Any]:
        """获取规范信息"""
        spec_class = self.get_spec(spec_type)
        if not spec_class:
            return {}
        
        spec_instance = spec_class()
        return {
            'spec_type': spec_type,
            'version': spec_instance.version,
            'description': getattr(spec_instance, '__doc__', ''),
            'has_parser': spec_type in self._parsers,
            'has_executor': spec_type in self._executors
        }
    
    def get_protocol_info(self, protocol_name: str) -> Dict[str, Any]:
        """获取协议信息"""
        protocol_class = self.get_protocol(protocol_name)
        if not protocol_class:
            return {}
        
        # 创建临时实例来获取协议信息
        temp_config = {}
        temp_adapter = protocol_class(temp_config)
        
        return {
            'protocol_name': protocol_name,
            'supported_operations': temp_adapter.get_supported_operations(),
            'description': getattr(protocol_class, '__doc__', '')
        }
    
    def validate_registration(self, spec_type: str) -> Dict[str, Any]:
        """验证注册完整性"""
        result = {
            'spec_type': spec_type,
            'has_spec': spec_type in self._specs,
            'has_parser': spec_type in self._parsers,
            'has_executor': spec_type in self._executors,
            'complete': False
        }
        
        result['complete'] = result['has_spec'] and result['has_parser'] and result['has_executor']
        return result
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """获取注册器摘要"""
        return {
            'specifications': {
                'count': len(self._specs),
                'types': self.list_specs()
            },
            'parsers': {
                'count': len(self._parsers),
                'types': self.list_parsers()
            },
            'executors': {
                'count': len(self._executors),
                'types': self.list_executors()
            },
            'protocols': {
                'count': len(self._protocols),
                'types': self.list_protocols()
            },
            'complete_registrations': [
                spec_type for spec_type in self.list_specs()
                if self.validate_registration(spec_type)['complete']
            ]
        }
    
    def unregister_spec(self, spec_type: str):
        """注销规范"""
        if spec_type in self._specs:
            del self._specs[spec_type]
            self.logger.info(f"Unregistered API specification: {spec_type}")
    
    def unregister_parser(self, spec_type: str):
        """注销解析器"""
        if spec_type in self._parsers:
            del self._parsers[spec_type]
            self.logger.info(f"Unregistered parser: {spec_type}")
    
    def unregister_executor(self, spec_type: str):
        """注销执行器"""
        if spec_type in self._executors:
            del self._executors[spec_type]
            self.logger.info(f"Unregistered executor: {spec_type}")
    
    def unregister_protocol(self, protocol_name: str):
        """注销协议适配器"""
        if protocol_name in self._protocols:
            del self._protocols[protocol_name]
            self.logger.info(f"Unregistered protocol adapter: {protocol_name}")
    
    def clear(self):
        """清空所有注册"""
        self._specs.clear()
        self._parsers.clear()
        self._executors.clear()
        self._protocols.clear()
        self.logger.info("Cleared all registrations") 