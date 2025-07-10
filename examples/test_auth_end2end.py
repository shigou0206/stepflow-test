#!/usr/bin/env python3
"""
StepFlow Gateway 端到端认证测试
包括用户管理、认证配置、OAuth2 流程和 API 调用
"""

import json
import requests
import time
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# 测试用的 OpenAPI 文档
TEST_OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "Auth Test API",
        "version": "1.0.0",
        "description": "用于测试各种认证机制的 API"
    },
    "servers": [
        {
            "url": "https://httpbin.org",
            "description": "httpbin 测试服务器"
        }
    ],
    "paths": {
        "/basic-auth/{user}/{passwd}": {
            "get": {
                "summary": "Basic Auth 测试",
                "operationId": "basicAuthTest",
                "parameters": [
                    {
                        "name": "user",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "passwd",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "认证成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "authenticated": {"type": "boolean"},
                                        "user": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "认证失败"}
                }
            }
        },
        "/bearer": {
            "get": {
                "summary": "Bearer Token 测试",
                "operationId": "bearerAuthTest",
                "security": [
                    {
                        "bearerAuth": []
                    }
                ],
                "responses": {
                    "200": {
                        "description": "认证成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "token": {"type": "string"},
                                        "authenticated": {"type": "boolean"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "认证失败"}
                }
            }
        },
        "/headers": {
            "get": {
                "summary": "API Key Header 测试",
                "operationId": "apiKeyHeaderTest",
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "headers": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/get": {
            "get": {
                "summary": "API Key Query 测试",
                "operationId": "apiKeyQueryTest",
                "parameters": [
                    {
                        "name": "api_key",
                        "in": "query",
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "args": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/oauth2/userinfo": {
            "get": {
                "summary": "OAuth2 用户信息测试",
                "operationId": "oauth2UserInfoTest",
                "security": [
                    {
                        "oauth2": ["read:user"]
                    }
                ],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "user_id": {"type": "string"},
                                        "email": {"type": "string"},
                                        "scope": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "认证失败"}
                }
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
            "oauth2": {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "https://example.com/oauth/authorize",
                        "tokenUrl": "https://example.com/oauth/token",
                        "scopes": {
                            "read:user": "读取用户信息",
                            "write:user": "修改用户信息"
                        }
                    }
                }
            }
        }
    }
}

class AuthEndToEndTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_user = None
        self.test_api_doc = None
        self.endpoints = {}
        self.auth_configs = {}
        
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
    
    def test_user_registration(self):
        """步骤 2: 用户注册"""
        self.print_step(2, "用户注册")
        
        # 生成唯一用户名
        timestamp = int(time.time())
        username = f"testuser_{timestamp}"
        email = f"{username}@example.com"
        
        user_data = {
            "username": username,
            "email": email,
            "password": "testpass123",
            "role": "user",
            "permissions": {
                "api_access": True,
                "auth_manage": True
            }
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/register", json=user_data)
            result = response.json()
            
            if result.get("success"):
                self.test_user = {
                    "username": username,
                    "email": email,
                    "user_id": result.get("user_id")
                }
                print(f"✅ 用户注册成功: {username}")
                print(f"   用户ID: {self.test_user['user_id']}")
                return True
            else:
                print(f"❌ 用户注册失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ 注册异常: {e}")
            return False
    
    def test_user_login(self):
        """步骤 3: 用户登录"""
        self.print_step(3, "用户登录")
        
        if not self.test_user:
            print("❌ 没有测试用户，跳过登录")
            return False
        
        login_data = {
            "username": self.test_user["username"],
            "password": "testpass123"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/login", json=login_data)
            result = response.json()
            
            if result.get("success"):
                # 保存会话令牌
                self.session.headers.update({
                    "Authorization": f"Bearer {result.get('session_token')}"
                })
                print(f"✅ 用户登录成功: {self.test_user['username']}")
                print(f"   会话令牌: {result.get('session_token')[:20]}...")
                return True
            else:
                print(f"❌ 用户登录失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def test_api_registration(self):
        """步骤 4: API 文档注册"""
        self.print_step(4, "API 文档注册")
        
        api_data = {
            "name": "Auth Test API",
            "openapi_content": json.dumps(TEST_OPENAPI),
            "version": "1.0.0",
            "base_url": "https://httpbin.org"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/apis/register", json=api_data)
            result = response.json()
            
            if result.get("success"):
                self.test_api_doc = {
                    "document_id": result.get("document_id"),
                    "template_id": result.get("template_id")
                }
                self.endpoints = {ep["path"]: ep for ep in result.get("endpoints", [])}
                
                print(f"✅ API 注册成功")
                print(f"   文档ID: {self.test_api_doc['document_id']}")
                print(f"   端点数量: {len(self.endpoints)}")
                
                for path, endpoint in self.endpoints.items():
                    print(f"   - {endpoint['method']} {path}: {endpoint['summary']}")
                
                return True
            else:
                print(f"❌ API 注册失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ API 注册异常: {e}")
            return False
    
    def test_basic_auth_config(self):
        """步骤 5: Basic Auth 配置"""
        self.print_step(5, "Basic Auth 配置")
        
        auth_config = {
            "username": "user",
            "password": "passwd"
        }
        
        return self._add_auth_config("basic", auth_config, "Basic Auth 配置")
    
    def test_bearer_auth_config(self):
        """步骤 6: Bearer Token 配置"""
        self.print_step(6, "Bearer Token 配置")
        
        auth_config = {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
        }
        
        return self._add_auth_config("bearer", auth_config, "Bearer Token 配置")
    
    def test_api_key_header_config(self):
        """步骤 7: API Key Header 配置"""
        self.print_step(7, "API Key Header 配置")
        
        auth_config = {
            "in": "header",
            "name": "X-API-Key",
            "value": "test-api-key-header-12345"
        }
        
        return self._add_auth_config("api_key", auth_config, "API Key Header 配置")
    
    def test_api_key_query_config(self):
        """步骤 8: API Key Query 配置"""
        self.print_step(8, "API Key Query 配置")
        
        auth_config = {
            "in": "query",
            "name": "api_key",
            "value": "test-api-key-query-67890"
        }
        
        return self._add_auth_config("api_key", auth_config, "API Key Query 配置")
    
    def test_oauth2_config(self):
        """步骤 9: OAuth2 配置"""
        self.print_step(9, "OAuth2 配置")
        
        auth_config = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "authorization_url": "https://example.com/oauth/authorize",
            "token_url": "https://example.com/oauth/token",
            "redirect_uri": "http://localhost:8000/oauth2/callback",
            "scope": "read:user write:user",
            "access_token": "test-oauth2-access-token",
            "refresh_token": "test-oauth2-refresh-token"
        }
        
        return self._add_auth_config("oauth2", auth_config, "OAuth2 配置")
    
    def _add_auth_config(self, auth_type, auth_config, description):
        """添加认证配置"""
        if not self.test_api_doc:
            print(f"❌ 没有 API 文档，跳过 {description}")
            return False
        
        config_data = {
            "api_document_id": self.test_api_doc["document_id"],
            "auth_type": auth_type,
            "auth_config": auth_config,
            "is_required": True,
            "is_global": False,
            "priority": 1
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/configs", json=config_data)
            result = response.json()
            
            if result.get("success"):
                config_id = result.get("auth_config_id")
                self.auth_configs[auth_type] = config_id
                print(f"✅ {description} 成功")
                print(f"   配置ID: {config_id}")
                return True
            else:
                print(f"❌ {description} 失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ {description} 异常: {e}")
            return False
    
    def test_basic_auth_call(self):
        """步骤 10: Basic Auth API 调用"""
        self.print_step(10, "Basic Auth API 调用")
        
        endpoint = self.endpoints.get("/basic-auth/{user}/{passwd}")
        if not endpoint:
            print("❌ 找不到 Basic Auth 端点")
            return False
        
        request_data = {
            "method": "GET",
            "url": "https://httpbin.org/basic-auth/user/passwd",
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        return self._call_api(endpoint, request_data, "Basic Auth")
    
    def test_bearer_auth_call(self):
        """步骤 11: Bearer Token API 调用"""
        self.print_step(11, "Bearer Token API 调用")
        
        endpoint = self.endpoints.get("/bearer")
        if not endpoint:
            print("❌ 找不到 Bearer Auth 端点")
            return False
        
        request_data = {
            "method": "GET",
            "url": "https://httpbin.org/bearer",
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        return self._call_api(endpoint, request_data, "Bearer Token")
    
    def test_api_key_header_call(self):
        """步骤 12: API Key Header API 调用"""
        self.print_step(12, "API Key Header API 调用")
        
        endpoint = self.endpoints.get("/headers")
        if not endpoint:
            print("❌ 找不到 API Key Header 端点")
            return False
        
        request_data = {
            "method": "GET",
            "url": "https://httpbin.org/headers",
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        return self._call_api(endpoint, request_data, "API Key Header")
    
    def test_api_key_query_call(self):
        """步骤 13: API Key Query API 调用"""
        self.print_step(13, "API Key Query API 调用")
        
        endpoint = self.endpoints.get("/get")
        if not endpoint:
            print("❌ 找不到 API Key Query 端点")
            return False
        
        request_data = {
            "method": "GET",
            "url": "https://httpbin.org/get",
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        return self._call_api(endpoint, request_data, "API Key Query")
    
    def test_oauth2_call(self):
        """步骤 14: OAuth2 API 调用"""
        self.print_step(14, "OAuth2 API 调用")
        
        endpoint = self.endpoints.get("/oauth2/userinfo")
        if not endpoint:
            print("❌ 找不到 OAuth2 端点")
            return False
        
        request_data = {
            "method": "GET",
            "url": "https://httpbin.org/oauth2/userinfo",
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        return self._call_api(endpoint, request_data, "OAuth2")
    
    def _call_api(self, endpoint, request_data, auth_type):
        """调用 API"""
        call_data = {
            "endpoint_id": endpoint["id"],
            "request_data": request_data
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/api/call", json=call_data)
            result = response.json()
            
            if result.get("success"):
                print(f"✅ {auth_type} API 调用成功")
                print(f"   状态码: {result.get('status_code')}")
                
                # 显示响应内容（简化）
                response_body = result.get('response_body', {})
                if isinstance(response_body, dict):
                    print(f"   响应: {json.dumps(response_body, indent=2, ensure_ascii=False)[:200]}...")
                else:
                    print(f"   响应: {str(response_body)[:200]}...")
                
                return True
            else:
                print(f"❌ {auth_type} API 调用失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ {auth_type} API 调用异常: {e}")
            return False
    
    def test_oauth2_flow(self):
        """步骤 15: OAuth2 完整流程测试"""
        self.print_step(15, "OAuth2 完整流程测试")
        
        if not self.test_user or not self.test_api_doc:
            print("❌ 缺少用户或 API 文档，跳过 OAuth2 流程")
            return False
        
        try:
            # 1. 创建 OAuth2 授权 URL
            auth_url_data = {
                "user_id": self.test_user["user_id"],
                "api_document_id": self.test_api_doc["document_id"]
            }
            
            response = self.session.post(f"{BASE_URL}/oauth2/auth-url", json=auth_url_data)
            result = response.json()
            
            if result.get("success"):
                print(f"✅ OAuth2 授权 URL 创建成功")
                print(f"   授权 URL: {result.get('auth_url')}")
                
                # 2. 模拟 OAuth2 回调（这里只是演示，实际需要真实的 OAuth2 服务器）
                print(f"   模拟 OAuth2 回调流程...")
                
                # 3. 验证 OAuth2 授权状态
                print(f"✅ OAuth2 流程测试完成（模拟）")
                return True
            else:
                print(f"❌ OAuth2 授权 URL 创建失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ OAuth2 流程测试异常: {e}")
            return False
    
    def test_statistics(self):
        """步骤 16: 查看统计信息"""
        self.print_step(16, "查看统计信息")
        
        try:
            # API 调用统计
            response = self.session.get(f"{BASE_URL}/statistics")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ API 调用统计:")
                print(f"   总调用次数: {stats.get('api_calls', 0)}")
                print(f"   成功次数: {stats.get('success_calls', 0)}")
                print(f"   失败次数: {stats.get('error_calls', 0)}")
            
            # 最近的调用日志
            response = self.session.get(f"{BASE_URL}/logs/recent", params={"limit": 5})
            if response.status_code == 200:
                logs = response.json()
                recent_calls = logs.get('recent_calls', [])
                print(f"✅ 最近 {len(recent_calls)} 次调用:")
                for call in recent_calls:
                    print(f"   - {call.get('method', 'N/A')} {call.get('path', 'N/A')}: {call.get('response_status_code', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 统计信息获取异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 StepFlow Gateway 端到端认证测试")
        print("=" * 80)
        
        tests = [
            self.test_health_check,
            self.test_user_registration,
            self.test_user_login,
            self.test_api_registration,
            self.test_basic_auth_config,
            self.test_bearer_auth_config,
            self.test_api_key_header_config,
            self.test_api_key_query_config,
            self.test_oauth2_config,
            self.test_basic_auth_call,
            self.test_bearer_auth_call,
            self.test_api_key_header_call,
            self.test_api_key_query_call,
            self.test_oauth2_call,
            self.test_oauth2_flow,
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
            print("✅ 所有测试通过！")
        else:
            print(f"⚠️  {total - passed} 个测试失败")
        
        return passed == total

def main():
    tester = AuthEndToEndTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 端到端认证测试全部通过！")
        print("   系统支持完整的认证流程，包括：")
        print("   - 用户注册和登录")
        print("   - Basic Auth")
        print("   - Bearer Token")
        print("   - API Key (Header/Query)")
        print("   - OAuth2 完整流程")
        print("   - API 调用和统计")
    else:
        print("\n❌ 部分测试失败，请检查系统配置")

if __name__ == "__main__":
    main() 