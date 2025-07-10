#!/usr/bin/env python3
"""
测试参数传递的各种方式
演示路径参数、查询参数、请求体、头部等参数传递
"""

import json
import requests
import time

BASE_URL = "http://localhost:8000"

# 测试用的 OpenAPI 文档，包含各种参数类型
TEST_OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "Parameter Test API",
        "version": "1.0.0",
        "description": "用于测试参数传递的 API"
    },
    "servers": [
        {
            "url": "https://httpbin.org",
            "description": "httpbin 测试服务器"
        }
    ],
    "paths": {
        "/users/{userId}": {
            "get": {
                "summary": "获取用户信息",
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "includeDetails",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "boolean", "default": False}
                    },
                    {
                        "name": "fields",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {"description": "成功"}
                }
            },
            "put": {
                "summary": "更新用户信息",
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string"},
                                    "age": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "成功"}
                }
            }
        },
        "/posts": {
            "get": {
                "summary": "获取文章列表",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 1}
                    },
                    {
                        "name": "size",
                        "in": "query",
                        "schema": {"type": "integer", "default": 10}
                    },
                    {
                        "name": "category",
                        "in": "query",
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "sort",
                        "in": "query",
                        "schema": {"type": "string", "enum": ["date", "title", "views"]}
                    }
                ],
                "responses": {
                    "200": {"description": "成功"}
                }
            },
            "post": {
                "summary": "创建新文章",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "content": {"type": "string"},
                                    "category": {"type": "string"},
                                    "tags": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "创建成功"}
                }
            }
        },
        "/users/{userId}/posts/{postId}": {
            "get": {
                "summary": "获取用户的特定文章",
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "postId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "version",
                        "in": "query",
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {"description": "成功"}
                }
            }
        }
    }
}

class ParameterPassingTest:
    def __init__(self):
        self.session = requests.Session()
        self.api_document_id = None
        
    def print_step(self, step_num, title):
        """打印测试步骤"""
        print(f"\n{'='*60}")
        print(f"步骤 {step_num}: {title}")
        print(f"{'='*60}")
    
    def test_api_registration(self):
        """步骤 1: 注册测试 API"""
        self.print_step(1, "注册测试 API")
        
        api_data = {
            "name": "Parameter Test API",
            "openapi_content": json.dumps(TEST_OPENAPI),
            "version": "1.0.0",
            "base_url": "https://httpbin.org"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/apis/register", json=api_data)
            result = response.json()
            
            if result.get("success"):
                self.api_document_id = result.get("document_id")
                print(f"✅ API 注册成功: {self.api_document_id}")
                return True
            else:
                print(f"❌ API 注册失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ API 注册异常: {e}")
            return False
    
    def test_path_parameters(self):
        """步骤 2: 测试路径参数传递"""
        self.print_step(2, "测试路径参数传递")
        
        if not self.api_document_id:
            print("❌ 没有 API 文档 ID")
            return False
        
        # 测试 GET /users/{userId}
        try:
            url = f"{BASE_URL}/api/call/path"
            params = {
                "path": "/users/123",
                "method": "GET",
                "api_document_id": self.api_document_id
            }
            
            request_data = {
                "params": {
                    "includeDetails": True,
                    "fields": "name,email,age"
                },
                "headers": {
                    "X-Request-ID": "test-123"
                }
            }
            
            response = self.session.post(url, params=params, json=request_data)
            result = response.json()
            
            if result.get("success"):
                print(f"✅ 路径参数测试成功")
                print(f"   请求路径: GET /users/123")
                print(f"   查询参数: includeDetails=true&fields=name,email,age")
                print(f"   响应状态: {result.get('response', {}).get('status_code')}")
                return True
            else:
                print(f"❌ 路径参数测试失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ 路径参数测试异常: {e}")
            return False
    
    def test_query_parameters(self):
        """步骤 3: 测试查询参数传递"""
        self.print_step(3, "测试查询参数传递")
        
        if not self.api_document_id:
            print("❌ 没有 API 文档 ID")
            return False
        
        # 测试 GET /posts
        try:
            url = f"{BASE_URL}/api/call/path"
            params = {
                "path": "/posts",
                "method": "GET",
                "api_document_id": self.api_document_id
            }
            
            request_data = {
                "params": {
                    "page": 2,
                    "size": 5,
                    "category": "technology",
                    "sort": "date"
                },
                "headers": {
                    "Accept": "application/json"
                }
            }
            
            response = self.session.post(url, params=params, json=request_data)
            result = response.json()
            
            if result.get("success"):
                print(f"✅ 查询参数测试成功")
                print(f"   请求路径: GET /posts")
                print(f"   查询参数: page=2&size=5&category=technology&sort=date")
                print(f"   响应状态: {result.get('response', {}).get('status_code')}")
                return True
            else:
                print(f"❌ 查询参数测试失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ 查询参数测试异常: {e}")
            return False
    
    def test_request_body(self):
        """步骤 4: 测试请求体传递"""
        self.print_step(4, "测试请求体传递")
        
        if not self.api_document_id:
            print("❌ 没有 API 文档 ID")
            return False
        
        # 测试 POST /posts
        try:
            url = f"{BASE_URL}/api/call/path"
            params = {
                "path": "/posts",
                "method": "POST",
                "api_document_id": self.api_document_id
            }
            
            request_data = {
                "body": {
                    "title": "测试文章标题",
                    "content": "这是测试文章的内容",
                    "category": "technology",
                    "tags": ["python", "api", "test"]
                },
                "headers": {
                    "Content-Type": "application/json",
                    "X-User-ID": "test-user-123"
                }
            }
            
            response = self.session.post(url, params=params, json=request_data)
            result = response.json()
            
            if result.get("success"):
                print(f"✅ 请求体测试成功")
                print(f"   请求路径: POST /posts")
                print(f"   请求体: {json.dumps(request_data['body'], ensure_ascii=False)}")
                print(f"   响应状态: {result.get('response', {}).get('status_code')}")
                return True
            else:
                print(f"❌ 请求体测试失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ 请求体测试异常: {e}")
            return False
    
    def test_complex_parameters(self):
        """步骤 5: 测试复杂参数组合"""
        self.print_step(5, "测试复杂参数组合")
        
        if not self.api_document_id:
            print("❌ 没有 API 文档 ID")
            return False
        
        # 测试 PUT /users/{userId}
        try:
            url = f"{BASE_URL}/api/call/path"
            params = {
                "path": "/users/456",
                "method": "PUT",
                "api_document_id": self.api_document_id
            }
            
            request_data = {
                "body": {
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "age": 28
                },
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token-123",
                    "X-Request-ID": "complex-test-456"
                },
                "params": {
                    "validate": True,
                    "notify": False
                }
            }
            
            response = self.session.post(url, params=params, json=request_data)
            result = response.json()
            
            if result.get("success"):
                print(f"✅ 复杂参数测试成功")
                print(f"   请求路径: PUT /users/456")
                print(f"   路径参数: userId=456")
                print(f"   查询参数: validate=true&notify=false")
                print(f"   请求体: {json.dumps(request_data['body'], ensure_ascii=False)}")
                print(f"   自定义头部: {request_data['headers']}")
                print(f"   响应状态: {result.get('response', {}).get('status_code')}")
                return True
            else:
                print(f"❌ 复杂参数测试失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ 复杂参数测试异常: {e}")
            return False
    
    def test_nested_path_parameters(self):
        """步骤 6: 测试嵌套路径参数"""
        self.print_step(6, "测试嵌套路径参数")
        
        if not self.api_document_id:
            print("❌ 没有 API 文档 ID")
            return False
        
        # 测试 GET /users/{userId}/posts/{postId}
        try:
            url = f"{BASE_URL}/api/call/path"
            params = {
                "path": "/users/789/posts/abc123",
                "method": "GET",
                "api_document_id": self.api_document_id
            }
            
            request_data = {
                "params": {
                    "version": "v2"
                },
                "headers": {
                    "Accept": "application/json",
                    "X-User-Agent": "ParameterTest/1.0"
                }
            }
            
            response = self.session.post(url, params=params, json=request_data)
            result = response.json()
            
            if result.get("success"):
                print(f"✅ 嵌套路径参数测试成功")
                print(f"   请求路径: GET /users/789/posts/abc123")
                print(f"   路径参数: userId=789, postId=abc123")
                print(f"   查询参数: version=v2")
                print(f"   响应状态: {result.get('response', {}).get('status_code')}")
                return True
            else:
                print(f"❌ 嵌套路径参数测试失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ 嵌套路径参数测试异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 StepFlow Gateway 参数传递测试")
        print("=" * 80)
        
        tests = [
            self.test_api_registration,
            self.test_path_parameters,
            self.test_query_parameters,
            self.test_request_body,
            self.test_complex_parameters,
            self.test_nested_path_parameters
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ 测试异常: {e}")
        
        print(f"\n{'='*80}")
        print(f"🎉 测试完成: {passed}/{total} 通过")
        print(f"{'='*80}")
        
        if passed == total:
            print("✅ 所有参数传递测试通过！")
            print("   参数传递功能正常工作！")
        else:
            print(f"⚠️  {total - passed} 个测试失败")
        
        return passed == total

def main():
    tester = ParameterPassingTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 参数传递设计总结：")
        print("   ✅ 路径参数：自动替换 {paramName} 占位符")
        print("   ✅ 查询参数：支持复杂查询条件")
        print("   ✅ 请求体：支持 JSON 格式数据")
        print("   ✅ HTTP 头部：支持自定义头部")
        print("   ✅ 参数组合：支持多种参数同时使用")
        print("   ✅ 嵌套路径：支持多级路径参数")
    else:
        print("\n❌ 部分参数传递功能需要修复")

if __name__ == "__main__":
    main() 