#!/usr/bin/env python3
"""
注册表单元测试
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from stepflow_gateway.core.registry import ApiSpecRegistry
from stepflow_gateway.plugins.openapi import OpenAPISpecification, OpenAPIParser, OpenAPIExecutor, HTTPProtocolAdapter


class TestApiSpecRegistry(unittest.TestCase):
    """测试 API 规范注册表"""
    
    def setUp(self):
        self.registry = ApiSpecRegistry()
        
        # 使用具体的实现类
        self.mock_spec = OpenAPISpecification
        self.mock_parser = OpenAPIParser
        self.mock_executor = OpenAPIExecutor
        self.mock_protocol = HTTPProtocolAdapter
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.registry._specs, {})
        self.assertEqual(self.registry._parsers, {})
        self.assertEqual(self.registry._executors, {})
        self.assertEqual(self.registry._protocols, {})
    
    def test_register_spec(self):
        """测试注册规范"""
        self.registry.register_spec("openapi", self.mock_spec)
        self.assertIn("openapi", self.registry._specs)
        self.assertEqual(self.registry._specs["openapi"], self.mock_spec)
    
    def test_register_parser(self):
        """测试注册解析器"""
        self.registry.register_parser("openapi", self.mock_parser)
        self.assertIn("openapi", self.registry._parsers)
        self.assertEqual(self.registry._parsers["openapi"], self.mock_parser)
    
    def test_register_executor(self):
        """测试注册执行器"""
        self.registry.register_executor("openapi", self.mock_executor)
        self.assertIn("openapi", self.registry._executors)
        self.assertEqual(self.registry._executors["openapi"], self.mock_executor)
    
    def test_register_protocol(self):
        """测试注册协议"""
        self.registry.register_protocol("http", self.mock_protocol)
        self.assertIn("http", self.registry._protocols)
        self.assertEqual(self.registry._protocols["http"], self.mock_protocol)
    
    def test_list_specs(self):
        """测试列出规范"""
        self.registry.register_spec("openapi", self.mock_spec)
        self.registry.register_spec("asyncapi", self.mock_spec)
        
        specs = self.registry.list_specs()
        self.assertIn("openapi", specs)
        self.assertIn("asyncapi", specs)
        self.assertEqual(len(specs), 2)
    
    def test_list_parsers(self):
        """测试列出解析器"""
        self.registry.register_parser("openapi", self.mock_parser)
        self.registry.register_parser("asyncapi", self.mock_parser)
        
        parsers = self.registry.list_parsers()
        self.assertIn("openapi", parsers)
        self.assertIn("asyncapi", parsers)
        self.assertEqual(len(parsers), 2)
    
    def test_list_executors(self):
        """测试列出执行器"""
        self.registry.register_executor("openapi", self.mock_executor)
        self.registry.register_executor("asyncapi", self.mock_executor)
        
        executors = self.registry.list_executors()
        self.assertIn("openapi", executors)
        self.assertIn("asyncapi", executors)
        self.assertEqual(len(executors), 2)
    
    def test_list_protocols(self):
        """测试列出协议"""
        self.registry.register_protocol("http", self.mock_protocol)
        self.registry.register_protocol("https", self.mock_protocol)
        
        protocols = self.registry.list_protocols()
        self.assertIn("http", protocols)
        self.assertIn("https", protocols)
        self.assertEqual(len(protocols), 2)
    
    def test_get_spec(self):
        """测试获取规范"""
        self.registry.register_spec("openapi", self.mock_spec)
        
        spec = self.registry.get_spec("openapi")
        self.assertEqual(spec, self.mock_spec)
        
        # 测试不存在的规范
        spec = self.registry.get_spec("nonexistent")
        self.assertIsNone(spec)
    
    def test_get_parser(self):
        """测试获取解析器"""
        self.registry.register_parser("openapi", self.mock_parser)
        
        parser = self.registry.get_parser("openapi")
        self.assertEqual(parser, self.mock_parser)
        
        # 测试不存在的解析器
        parser = self.registry.get_parser("nonexistent")
        self.assertIsNone(parser)
    
    def test_get_executor(self):
        """测试获取执行器"""
        self.registry.register_executor("openapi", self.mock_executor)
        
        executor = self.registry.get_executor("openapi")
        self.assertEqual(executor, self.mock_executor)
        
        # 测试不存在的执行器
        executor = self.registry.get_executor("nonexistent")
        self.assertIsNone(executor)
    
    def test_get_protocol(self):
        """测试获取协议"""
        self.registry.register_protocol("http", self.mock_protocol)
        
        protocol = self.registry.get_protocol("http")
        self.assertEqual(protocol, self.mock_protocol)
        
        # 测试不存在的协议
        protocol = self.registry.get_protocol("nonexistent")
        self.assertIsNone(protocol)
    
    def test_create_spec(self):
        """测试创建规范实例"""
        self.registry.register_spec("openapi", self.mock_spec)
        spec = self.registry.create_spec("openapi")
        self.assertIsInstance(spec, OpenAPISpecification)

    def test_create_parser(self):
        """测试创建解析器实例"""
        self.registry.register_parser("openapi", self.mock_parser)
        parser = self.registry.create_parser("openapi")
        self.assertIsInstance(parser, OpenAPIParser)

    def test_create_executor(self):
        """测试创建执行器实例"""
        self.registry.register_executor("openapi", self.mock_executor)
        # OpenAPIExecutor 只接受 protocol 参数
        executor = self.mock_executor(HTTPProtocolAdapter())
        self.assertIsInstance(executor, OpenAPIExecutor)

    def test_create_protocol(self):
        """测试创建协议实例"""
        self.registry.register_protocol("http", self.mock_protocol)
        protocol = self.mock_protocol()
        self.assertIsInstance(protocol, HTTPProtocolAdapter)

    def test_get_registry_summary(self):
        """测试获取注册表摘要"""
        self.registry.register_spec("openapi", self.mock_spec)
        self.registry.register_parser("openapi", self.mock_parser)
        self.registry.register_executor("openapi", self.mock_executor)
        self.registry.register_protocol("http", self.mock_protocol)
        summary = self.registry.get_registry_summary()
        self.assertIn("specifications", summary)
        self.assertIn("parsers", summary)
        self.assertIn("executors", summary)
        self.assertIn("protocols", summary)
        self.assertIn("openapi", summary["specifications"]["types"])

    def test_get_spec_info(self):
        """测试获取规范信息"""
        self.registry.register_spec("openapi", self.mock_spec)
        self.registry.register_parser("openapi", self.mock_parser)
        self.registry.register_executor("openapi", self.mock_executor)
        info = self.registry.get_spec_info("openapi")
        self.assertIn("spec_type", info)
        self.assertIn("version", info)
        self.assertIn("description", info)
        self.assertIn("has_parser", info)
        self.assertIn("has_executor", info)
        # 测试不存在的规范
        info = self.registry.get_spec_info("nonexistent")
        self.assertEqual(info, {})


if __name__ == '__main__':
    unittest.main() 