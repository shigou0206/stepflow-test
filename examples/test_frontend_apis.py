#!/usr/bin/env python3
"""
测试前端渲染相关的所有接口
验证新增的接口是否正常工作
"""

import json
import requests
import time

BASE_URL = "http://localhost:8000"

# 测试用的 OpenAPI 文档
TEST_OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "Frontend Test API",
        "version": "1.0.0",
        "description": "用于测试前端渲染接口的 API"
    },
    "servers": [
        {
            "url": "https://httpbin.org",
            "description": "httpbin 测试服务器"
        }
    ],
    "tags": [
        {
            "name": "pets",
            "description": "宠物相关接口"
        },
        {
            "name": "users",
            "description": "用户相关接口"
        }
    ],
    "paths": {
        "/pets/{petId}": {
            "get": {
                "tags": ["pets"],
                "summary": "获取宠物信息",
                "description": "根据宠物ID获取详细信息",
                "operationId": "getPetById",
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "description": "宠物ID",
                        "schema": {
                            "type": "string",
                            "example": "123"
                        }
                    },
                    {
                        "name": "includeDetails",
                        "in": "query",
                        "required": False,
                        "description": "是否包含详细信息",
                        "schema": {
                            "type": "boolean",
                            "default": False
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "成功获取宠物信息",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "name": {"type": "string"},
                                        "type": {"type": "string"},
                                        "age": {"type": "integer"}
                                    }
                                },
                                "example": {
                                    "id": "123",
                                    "name": "小白",
                                    "type": "dog",
                                    "age": 3
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "宠物不存在"
                    }
                },
                "security": [
                    {
                        "bearerAuth": []
                    }
                ]
            },
            "put": {
                "tags": ["pets"],
                "summary": "更新宠物信息",
                "description": "更新指定宠物的信息",
                "operationId": "updatePet",
                "parameters": [
                    {
                        "name": "petId",
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
                                    "type": {"type": "string"},
                                    "age": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "更新成功"
                    }
                }
            }
        },
        "/users": {
            "get": {
                "tags": ["users"],
                "summary": "获取用户列表",
                "description": "获取所有用户的基本信息",
                "operationId": "getUsers",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {
                            "type": "integer",
                            "default": 1
                        }
                    },
                    {
                        "name": "size",
                        "in": "query",
                        "schema": {
                            "type": "integer",
                            "default": 10
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "成功获取用户列表",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "security": [
                    {
                        "apiKeyAuth": []
                    }
                ]
            }
        }
    },
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            },
            "apiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }
    }
}

class FrontendAPITest:
    def __init__(self):
        self.session = requests.Session()
        self.test_api_id = None
        self.test_endpoints = []
        self.test_auth_configs = []
        
    def print_step(self, step_num, title):
        """打印测试步骤"""
        print(f"\n{'='*60}")
        print(f"步骤 {step_num}: {title}")
        print(f"{'='*60}")
    
    def test_health_check(self):
        """步骤 1: 健康检查"""
        self.print_step(1, "健康检查")
        
        try:
            response = self.session.get(f"{BASE_URL}/health")
            print(f"✅ 服务状态: {response.status_code}")
            print(f"   响应: {response.json()}")
            return True
        except Exception as e:
            print(f"❌ 服务不可用: {e}")
            return False
    
    def test_api_registration(self):
        """步骤 2: 注册测试 API"""
        self.print_step(2, "注册测试 API")
        
        api_data = {
            "name": "Frontend Test API",
            "openapi_content": json.dumps(TEST_OPENAPI),
            "version": "1.0.0",
            "base_url": "https://httpbin.org"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/apis/register", json=api_data)
            result = response.json()
            
            if result.get("success"):
                self.test_api_id = result.get("document_id")
                self.test_endpoints = result.get("endpoints", [])
                print(f"✅ API 注册成功: {self.test_api_id}")
                print(f"   端点数量: {len(self.test_endpoints)}")
                return True
            else:
                print(f"❌ API 注册失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ API 注册异常: {e}")
            return False
    
    def test_get_openapi_doc(self):
        """步骤 3: 获取 OpenAPI 原文档"""
        self.print_step(3, "获取 OpenAPI 原文档")
        
        if not self.test_api_id:
            print("❌ 没有测试 API ID")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/apis/{self.test_api_id}/openapi")
            result = response.json()
            
            if result.get("success"):
                openapi_doc = result.get("openapi", {})
                print(f"✅ OpenAPI 文档获取成功")
                print(f"   标题: {openapi_doc.get('info', {}).get('title')}")
                print(f"   版本: {openapi_doc.get('info', {}).get('version')}")
                print(f"   路径数量: {len(openapi_doc.get('paths', {}))}")
                print(f"   Tags: {[tag.get('name') for tag in openapi_doc.get('tags', [])]}")
                return True
            else:
                print(f"❌ OpenAPI 文档获取失败")
                return False
                
        except Exception as e:
            print(f"❌ OpenAPI 文档获取异常: {e}")
            return False
    
    def test_get_api_tags(self):
        """步骤 4: 获取 API Tags"""
        self.print_step(4, "获取 API Tags")
        
        if not self.test_api_id:
            print("❌ 没有测试 API ID")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/apis/{self.test_api_id}/tags")
            result = response.json()
            
            if result.get("success"):
                tags = result.get("tags", [])
                print(f"✅ API Tags 获取成功")
                print(f"   Tags: {[tag.get('name') for tag in tags]}")
                return True
            else:
                print(f"❌ API Tags 获取失败")
                return False
                
        except Exception as e:
            print(f"❌ API Tags 获取异常: {e}")
            return False
    
    def test_get_api_summary(self):
        """步骤 5: 获取 API 摘要信息"""
        self.print_step(5, "获取 API 摘要信息")
        
        if not self.test_api_id:
            print("❌ 没有测试 API ID")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/apis/{self.test_api_id}/summary")
            result = response.json()
            
            if result.get("success"):
                summary = result.get("summary", {})
                print(f"✅ API 摘要获取成功")
                print(f"   名称: {summary.get('name')}")
                print(f"   版本: {summary.get('version')}")
                print(f"   端点数量: {summary.get('endpoint_count')}")
                print(f"   认证配置数量: {summary.get('auth_config_count')}")
                print(f"   最近调用次数: {summary.get('recent_call_count')}")
                return True
            else:
                print(f"❌ API 摘要获取失败")
                return False
                
        except Exception as e:
            print(f"❌ API 摘要获取异常: {e}")
            return False
    
    def test_get_detailed_endpoints(self):
        """步骤 6: 获取详细端点信息"""
        self.print_step(6, "获取详细端点信息")
        
        if not self.test_api_id:
            print("❌ 没有测试 API ID")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/endpoints", params={"api_document_id": self.test_api_id})
            result = response.json()
            
            if result.get("success"):
                endpoints = result.get("endpoints", [])
                print(f"✅ 详细端点信息获取成功")
                print(f"   端点数量: {len(endpoints)}")
                
                for ep in endpoints:
                    print(f"   - {ep.get('method')} {ep.get('path')}")
                    print(f"     摘要: {ep.get('summary')}")
                    print(f"     参数数量: {len(ep.get('parameters', []))}")
                    print(f"     Tags: {ep.get('tags', [])}")
                    print(f"     Security: {ep.get('security', [])}")
                    print()
                
                return True
            else:
                print(f"❌ 详细端点信息获取失败")
                return False
                
        except Exception as e:
            print(f"❌ 详细端点信息获取异常: {e}")
            return False
    
    def test_search_endpoints(self):
        """步骤 7: 搜索端点"""
        self.print_step(7, "搜索端点")
        
        if not self.test_api_id:
            print("❌ 没有测试 API ID")
            return False
        
        # 测试搜索
        search_queries = ["pets", "users", "get", "POST", "宠物"]
        success_count = 0
        
        for query in search_queries:
            try:
                response = self.session.get(f"{BASE_URL}/endpoints/search", params={
                    "q": query,
                    "api_document_id": self.test_api_id
                })
                result = response.json()
                
                if result.get("success"):
                    endpoints = result.get("endpoints", [])
                    print(f"✅ 搜索 '{query}' 成功，找到 {len(endpoints)} 个端点")
                    for ep in endpoints:
                        print(f"   - {ep.get('method')} {ep.get('path')}: {ep.get('summary')}")
                    success_count += 1
                else:
                    print(f"❌ 搜索 '{query}' 失败")
                    
            except Exception as e:
                print(f"❌ 搜索 '{query}' 异常: {e}")
        
        return success_count > 0
    
    def test_auth_config_management(self):
        """步骤 8: 认证配置管理"""
        self.print_step(8, "认证配置管理")
        
        if not self.test_api_id:
            print("❌ 没有测试 API ID")
            return False
        
        # 添加认证配置
        auth_configs = [
            {
                "auth_type": "bearer",
                "auth_config": {"token": "test-bearer-token"},
                "description": "Bearer Token 配置"
            },
            {
                "auth_type": "api_key",
                "auth_config": {"in": "header", "name": "X-API-Key", "value": "test-api-key"},
                "description": "API Key Header 配置"
            },
            {
                "auth_type": "basic",
                "auth_config": {"username": "user", "password": "pass"},
                "description": "Basic Auth 配置"
            }
        ]
        
        for config in auth_configs:
            try:
                config_data = {
                    "api_document_id": self.test_api_id,
                    "auth_type": config["auth_type"],
                    "auth_config": config["auth_config"],
                    "is_required": True,
                    "is_global": False,
                    "priority": 1
                }
                
                response = self.session.post(f"{BASE_URL}/auth/configs", json=config_data)
                result = response.json()
                
                if result.get("success"):
                    config_id = result.get("auth_config_id")
                    self.test_auth_configs.append(config_id)
                    print(f"✅ {config['description']} 添加成功: {config_id}")
                else:
                    print(f"❌ {config['description']} 添加失败: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ {config['description']} 添加异常: {e}")
        
        # 获取认证配置列表
        try:
            response = self.session.get(f"{BASE_URL}/auth/configs", params={"api_document_id": self.test_api_id})
            result = response.json()
            
            if result.get("success"):
                configs = result.get("auth_configs", [])
                print(f"✅ 认证配置列表获取成功，共 {len(configs)} 个配置")
                
                for config in configs:
                    print(f"   - {config.get('auth_type')}: {config.get('id')}")
                    print(f"     配置: {config.get('auth_config_parsed')}")
                    print(f"     必需: {config.get('is_required')}")
                    print(f"     全局: {config.get('is_global')}")
                    print()
                
                return True
            else:
                print(f"❌ 认证配置列表获取失败")
                return False
                
        except Exception as e:
            print(f"❌ 认证配置列表获取异常: {e}")
            return False
    
    def test_get_recent_calls(self):
        """步骤 9: 获取最近调用日志"""
        self.print_step(9, "获取最近调用日志")
        
        try:
            # 获取所有调用
            response = self.session.get(f"{BASE_URL}/logs/recent", params={"limit": 10})
            result = response.json()
            
            if result.get("success"):
                calls = result.get("recent_calls", [])
                print(f"✅ 最近调用日志获取成功，共 {len(calls)} 条记录")
                
                for call in calls[:3]:  # 只显示前3条
                    print(f"   - {call.get('request_method')} {call.get('request_url')}")
                    print(f"     状态码: {call.get('response_status_code')}")
                    print(f"     响应时间: {call.get('response_time_ms')}ms")
                    print()
                
                return True
            else:
                print(f"❌ 最近调用日志获取失败")
                return False
                
        except Exception as e:
            print(f"❌ 最近调用日志获取异常: {e}")
            return False
    
    def test_statistics(self):
        """步骤 10: 获取统计信息"""
        self.print_step(10, "获取统计信息")
        
        try:
            response = self.session.get(f"{BASE_URL}/statistics")
            result = response.json()
            
            if result.get("success"):
                stats = result
                print(f"✅ 统计信息获取成功")
                print(f"   API 调用次数: {stats.get('api_calls', 0)}")
                print(f"   成功次数: {stats.get('success_calls', 0)}")
                print(f"   失败次数: {stats.get('error_calls', 0)}")
                print(f"   平均响应时间: {stats.get('avg_response_time_ms', 0)}ms")
                return True
            else:
                print(f"❌ 统计信息获取失败")
                return False
                
        except Exception as e:
            print(f"❌ 统计信息获取异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 StepFlow Gateway 前端渲染接口测试")
        print("=" * 80)
        
        tests = [
            self.test_health_check,
            self.test_api_registration,
            self.test_get_openapi_doc,
            self.test_get_api_tags,
            self.test_get_api_summary,
            self.test_get_detailed_endpoints,
            self.test_search_endpoints,
            self.test_auth_config_management,
            self.test_get_recent_calls,
            self.test_statistics
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
            print("✅ 所有前端渲染接口测试通过！")
            print("   现在可以开始开发前端界面了！")
        else:
            print(f"⚠️  {total - passed} 个测试失败")
        
        return passed == total

def main():
    tester = FrontendAPITest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 前端渲染接口全部就绪！")
        print("   支持的功能：")
        print("   ✅ OpenAPI 原文档获取")
        print("   ✅ 详细端点信息（参数、响应、tags、security）")
        print("   ✅ API Tags 分组")
        print("   ✅ API 摘要信息")
        print("   ✅ 端点搜索功能")
        print("   ✅ 认证配置管理")
        print("   ✅ 调用日志查询")
        print("   ✅ 统计信息")
        print("\n   前端可以基于这些接口实现类似 Swagger UI 的体验！")
    else:
        print("\n❌ 部分接口需要修复")

if __name__ == "__main__":
    main() 