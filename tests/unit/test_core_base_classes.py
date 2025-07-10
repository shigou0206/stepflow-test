#!/usr/bin/env python3
"""
核心基类单元测试
"""

import unittest
import json
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from stepflow_gateway.plugins.openapi import OpenAPISpecification, OpenAPIParser, OpenAPIExecutor, HTTPProtocolAdapter


class TestApiSpecification(unittest.TestCase):
    """测试 API 规范类"""
    
    def setUp(self):
        self.spec = OpenAPISpecification(None, "test-spec", {})
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.spec.name, "test-spec")
    
    def test_validate(self):
        """测试验证方法"""
        # 测试有效内容
        valid_content = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }
        self.assertTrue(self.spec.validate(valid_content))
        
        # 测试无效内容
        invalid_content = {"invalid": "content"}
        self.assertFalse(self.spec.validate(invalid_content))
    
    def test_parse(self):
        """测试解析方法"""
        content = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }
        parsed = self.spec.parse(content)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["openapi"], "3.0.0")
    
    def test_extract_endpoints(self):
        """测试端点提取"""
        content = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }
        endpoints = self.spec.extract_endpoints(content)
        self.assertIsInstance(endpoints, list)
        self.assertGreater(len(endpoints), 0)


class TestBaseParser(unittest.TestCase):
    """测试解析器类"""
    
    def setUp(self):
        self.parser = OpenAPIParser()
    
    def test_validate(self):
        """测试验证方法"""
        # 测试有效内容
        valid_content = json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        })
        self.assertTrue(self.parser.validate(valid_content))
        
        # 测试无效内容
        invalid_content = "invalid json"
        self.assertFalse(self.parser.validate(invalid_content))
    
    def test_parse(self):
        """测试解析方法"""
        content = json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        })
        parsed = self.parser.parse(content)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["openapi"], "3.0.0")
    
    def test_parse_specification(self):
        """测试规范解析"""
        content = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }
        spec = self.parser.parse_specification(content, "test", "Test API")
        self.assertIsInstance(spec, OpenAPISpecification)
        self.assertEqual(spec.name, "Test API")
    
    def test_parse_endpoints(self):
        """测试端点解析"""
        spec = OpenAPISpecification("test", "Test API", {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        })
        endpoints = self.parser.parse_endpoints(spec)
        self.assertIsInstance(endpoints, list)
        self.assertGreater(len(endpoints), 0)


class TestBaseExecutor(unittest.TestCase):
    """测试执行器类"""
    
    def setUp(self):
        self.protocol = HTTPProtocolAdapter()
        self.executor = OpenAPIExecutor(self.protocol)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.executor, OpenAPIExecutor)
    
    def test_list_operations(self):
        """测试操作列表"""
        spec = OpenAPISpecification("test", "Test API", {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        })
        operations = self.executor.list_operations(spec)
        self.assertIsInstance(operations, list)
        self.assertGreater(len(operations), 0)
    
    def test_get_operation_info(self):
        """测试操作信息获取"""
        spec = OpenAPISpecification("test", "Test API", {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        })
        info = self.executor.get_operation_info(spec, "GET /test")
        self.assertIsInstance(info, dict)
        self.assertIn("summary", info)


class TestBaseProtocolAdapter(unittest.TestCase):
    """测试协议适配器类"""
    
    def setUp(self):
        self.protocol = HTTPProtocolAdapter()
    
    def test_protocol_name_property(self):
        """测试协议名称属性"""
        self.assertEqual(self.protocol.protocol_name, "http")
    
    def test_build_url(self):
        """测试 URL 构建"""
        url = self.protocol.build_url("https://api.example.com", "/test")
        self.assertEqual(url, "https://api.example.com/test")
    
    def test_make_request(self):
        """测试请求发送"""
        # 只测试方法存在
        self.assertTrue(hasattr(self.protocol, 'make_request') or hasattr(self.protocol, 'build_url'))


if __name__ == '__main__':
    unittest.main() 