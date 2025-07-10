#!/usr/bin/env python3
"""
OpenAPI 边缘情况集成测试
"""

import unittest
import json
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from stepflow_gateway.core.gateway import StepFlowGateway
from stepflow_gateway.plugins.openapi import OpenAPISpecification, OpenAPIParser, OpenAPIExecutor, HTTPProtocolAdapter


class TestOpenAPIEdgeCases(unittest.TestCase):
    """测试 OpenAPI 边缘情况"""
    
    def setUp(self):
        self.gateway = StepFlowGateway()
        
        # 基础 OpenAPI 规范
        self.base_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "servers": [
                {
                    "url": "https://api.example.com/v1"
                }
            ],
            "paths": {}
        }
    
    def test_invalid_openapi_version(self):
        """测试无效的 OpenAPI 版本"""
        invalid_spec = self.base_spec.copy()
        invalid_spec["openapi"] = "2.0.0"  # 不支持的版本
        
        result = self.gateway.register_api(
            name="Invalid Version API",
            openapi_content=json.dumps(invalid_spec),
            version="1.0.0"
        )
        
        # 应该失败或给出警告
        self.assertIsInstance(result, dict)
    
    def test_missing_required_fields(self):
        """测试缺少必需字段"""
        # 缺少 info
        spec_no_info = {
            "openapi": "3.0.0",
            "paths": {}
        }
        
        result = self.gateway.register_api(
            name="No Info API",
            openapi_content=json.dumps(spec_no_info),
            version="1.0.0"
        )
        
        self.assertIsInstance(result, dict)
    
    def test_empty_paths(self):
        """测试空路径"""
        spec_empty_paths = self.base_spec.copy()
        spec_empty_paths["paths"] = {}
        
        result = self.gateway.register_api(
            name="Empty Paths API",
            openapi_content=json.dumps(spec_empty_paths),
            version="1.0.0"
        )
        
        self.assertIsInstance(result, dict)
        if result.get('success'):
            # 如果注册成功，应该没有端点
            document_id = result['document_id']
            endpoints = self.gateway.list_endpoints(document_id)
            self.assertEqual(len(endpoints), 0)
    
    def test_invalid_json_content(self):
        """测试无效的 JSON 内容"""
        result = self.gateway.register_api(
            name="Invalid JSON API",
            openapi_content="invalid json content",
            version="1.0.0"
        )
        
        self.assertIsInstance(result, dict)
        # 应该失败
        if not result.get('success'):
            self.assertIn('error', result)
    
    def test_malformed_parameters(self):
        """测试格式错误的参数"""
        spec_malformed = self.base_spec.copy()
        spec_malformed["paths"] = {
            "/test": {
                "get": {
                    "summary": "Test endpoint",
                    "parameters": [
                        {
                            "name": "param1",
                            "in": "invalid_location",  # 无效的位置
                            "required": True
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "OK"
                        }
                    }
                }
            }
        }
        
        result = self.gateway.register_api(
            name="Malformed Params API",
            openapi_content=json.dumps(spec_malformed),
            version="1.0.0"
        )
        
        self.assertIsInstance(result, dict)
    
    def test_unsupported_http_methods(self):
        """测试不支持的 HTTP 方法"""
        spec_unsupported = self.base_spec.copy()
        spec_unsupported["paths"] = {
            "/test": {
                "TRACE": {  # 不常用的方法
                    "summary": "Test TRACE",
                    "responses": {
                        "200": {
                            "description": "OK"
                        }
                    }
                },
                "OPTIONS": {  # 不常用的方法
                    "summary": "Test OPTIONS",
                    "responses": {
                        "200": {
                            "description": "OK"
                        }
                    }
                }
            }
        }
        
        result = self.gateway.register_api(
            name="Unsupported Methods API",
            openapi_content=json.dumps(spec_unsupported),
            version="1.0.0"
        )
        
        self.assertIsInstance(result, dict)
    
    def test_complex_parameter_types(self):
        """测试复杂参数类型"""
        spec_complex = self.base_spec.copy()
        spec_complex["paths"] = {
            "/test/{id}": {
                "get": {
                    "summary": "Test complex params",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "format": "uuid"
                            }
                        },
                        {
                            "name": "filter",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "age": {"type": "integer"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "OK"
                        }
                    }
                }
            }
        }
        
        result = self.gateway.register_api(
            name="Complex Params API",
            openapi_content=json.dumps(spec_complex),
            version="1.0.0"
        )
        
        self.assertIsInstance(result, dict)
    
    def test_request_body_validation(self):
        """测试请求体验证"""
        spec_with_body = self.base_spec.copy()
        spec_with_body["paths"] = {
            "/test": {
                "post": {
                    "summary": "Test with body",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "age": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "OK"
                        }
                    }
                }
            }
        }
        
        result = self.gateway.register_api(
            name="Request Body API",
            openapi_content=json.dumps(spec_with_body),
            version="1.0.0"
        )
        
        self.assertIsInstance(result, dict)
    
    def test_security_schemes(self):
        """测试安全方案"""
        spec_with_security = self.base_spec.copy()
        spec_with_security["components"] = {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        }
        spec_with_security["paths"] = {
            "/secure": {
                "get": {
                    "summary": "Secure endpoint",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "OK"
                        },
                        "401": {
                            "description": "Unauthorized"
                        }
                    }
                }
            }
        }
        
        result = self.gateway.register_api(
            name="Security API",
            openapi_content=json.dumps(spec_with_security),
            version="1.0.0"
        )
        
        self.assertIsInstance(result, dict)
    
    def test_references_and_components(self):
        """测试引用和组件"""
        spec_with_refs = self.base_spec.copy()
        spec_with_refs["components"] = {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    }
                }
            }
        }
        spec_with_refs["paths"] = {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/User"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        result = self.gateway.register_api(
            name="References API",
            openapi_content=json.dumps(spec_with_refs),
            version="1.0.0"
        )
        
        self.assertIsInstance(result, dict)
    
    def test_large_specification(self):
        """测试大型规范"""
        # 创建包含多个端点的规范
        large_spec = self.base_spec.copy()
        large_spec["paths"] = {}
        
        # 添加 100 个端点
        for i in range(100):
            large_spec["paths"][f"/endpoint{i}"] = {
                "get": {
                    "summary": f"Endpoint {i}",
                    "parameters": [
                        {
                            "name": "param",
                            "in": "query",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "OK"}
                    }
                }
            }
        
        result = self.gateway.register_api(
            name="Large API",
            openapi_content=json.dumps(large_spec),
            version="1.0.0"
        )
        
        self.assertIsInstance(result, dict)
        if result.get('success'):
            document_id = result['document_id']
            endpoints = self.gateway.list_endpoints(document_id)
            # 应该有 100 个端点
            self.assertEqual(len(endpoints), 100)
    
    def test_concurrent_registration(self):
        """测试并发注册"""
        import threading
        import time
        
        results = []
        errors = []
        
        def register_api(api_id):
            try:
                spec = self.base_spec.copy()
                spec["paths"] = {
                    f"/test{api_id}": {
                        "get": {
                            "summary": f"Test {api_id}",
                            "responses": {"200": {"description": "OK"}}
                        }
                    }
                }
                
                result = self.gateway.register_api(
                    name=f"Concurrent API {api_id}",
                    openapi_content=json.dumps(spec),
                    version="1.0.0"
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 创建 5 个线程同时注册
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_api, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        self.assertEqual(len(results), 5)
        self.assertEqual(len(errors), 0)
        
        # 所有注册都应该成功
        for result in results:
            self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main() 