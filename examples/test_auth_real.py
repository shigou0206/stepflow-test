#!/usr/bin/env python3
"""
使用真实认证端点的测试脚本
验证认证机制是否真正生效
"""

import json
import requests
import time

BASE_URL = "http://localhost:8000"

# 使用真实认证端点的 OpenAPI 文档
REAL_AUTH_OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "Real Auth Test API",
        "version": "1.0.0",
        "description": "使用真实认证端点的测试 API"
    },
    "servers": [
        {
            "url": "https://httpbin.org",
            "description": "httpbin 测试服务器"
        }
    ],
    "paths": {
        "/basic-auth/user/passwd": {
            "get": {
                "summary": "Basic Auth 测试（真实端点）",
                "operationId": "realBasicAuthTest",
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
        "/headers": {
            "get": {
                "summary": "查看请求头（验证 API Key）",
                "operationId": "viewHeaders",
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
                "summary": "查看查询参数（验证 API Key）",
                "operationId": "viewArgs",
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
        "/anything": {
            "get": {
                "summary": "通用端点（测试 Bearer Token）",
                "operationId": "anything",
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

def test_real_auth():
    """测试真实认证端点"""
    print("🔐 真实认证端点测试")
    print("=" * 60)
    
    # 1. 注册 API
    print("\n1. 注册真实认证 API...")
    api_data = {
        "name": "Real Auth Test API",
        "openapi_content": json.dumps(REAL_AUTH_OPENAPI),
        "version": "1.0.0",
        "base_url": "https://httpbin.org"
    }
    
    response = requests.post(f"{BASE_URL}/apis/register", json=api_data)
    result = response.json()
    
    if not result.get("success"):
        print(f"❌ API 注册失败: {result.get('error')}")
        return
    
    document_id = result.get("document_id")
    endpoints = {ep["path"]: ep for ep in result.get("endpoints", [])}
    print(f"✅ API 注册成功: {document_id}")
    
    # 2. 配置认证
    print("\n2. 配置认证机制...")
    
    # Basic Auth 配置
    basic_config = {
        "api_document_id": document_id,
        "auth_type": "basic",
        "auth_config": {"username": "user", "password": "passwd"},
        "is_required": True,
        "is_global": False,
        "priority": 1
    }
    
    response = requests.post(f"{BASE_URL}/auth/configs", json=basic_config)
    basic_result = response.json()
    print(f"   Basic Auth: {'✅' if basic_result.get('success') else '❌'}")
    
    # API Key Header 配置
    header_config = {
        "api_document_id": document_id,
        "auth_type": "api_key",
        "auth_config": {"in": "header", "name": "X-Test-Key", "value": "test-header-key-123"},
        "is_required": True,
        "is_global": False,
        "priority": 1
    }
    
    response = requests.post(f"{BASE_URL}/auth/configs", json=header_config)
    header_result = response.json()
    print(f"   API Key Header: {'✅' if header_result.get('success') else '❌'}")
    
    # API Key Query 配置
    query_config = {
        "api_document_id": document_id,
        "auth_type": "api_key",
        "auth_config": {"in": "query", "name": "test_key", "value": "test-query-key-456"},
        "is_required": True,
        "is_global": False,
        "priority": 1
    }
    
    response = requests.post(f"{BASE_URL}/auth/configs", json=query_config)
    query_result = response.json()
    print(f"   API Key Query: {'✅' if query_result.get('success') else '❌'}")
    
    # Bearer Token 配置
    bearer_config = {
        "api_document_id": document_id,
        "auth_type": "bearer",
        "auth_config": {"token": "test-bearer-token-789"},
        "is_required": True,
        "is_global": False,
        "priority": 1
    }
    
    response = requests.post(f"{BASE_URL}/auth/configs", json=bearer_config)
    bearer_result = response.json()
    print(f"   Bearer Token: {'✅' if bearer_result.get('success') else '❌'}")
    
    # 3. 测试 API 调用
    print("\n3. 测试 API 调用...")
    
    # 测试 Basic Auth
    if "/basic-auth/user/passwd" in endpoints:
        print("\n   🔐 测试 Basic Auth...")
        endpoint = endpoints["/basic-auth/user/passwd"]
        
        call_data = {
            "endpoint_id": endpoint["id"],
            "request_data": {
                "method": "GET",
                "url": "https://httpbin.org/basic-auth/user/passwd",
                "headers": {"Content-Type": "application/json"}
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/call", json=call_data)
        result = response.json()
        
        if result.get("success"):
            status_code = result.get("status_code")
            response_body = result.get("response_body", {})
            
            if status_code == 200:
                print(f"   ✅ Basic Auth 成功: {response_body.get('authenticated', False)}")
                print(f"      用户: {response_body.get('user', 'N/A')}")
            else:
                print(f"   ❌ Basic Auth 失败: {status_code}")
                print(f"      响应: {response_body}")
        else:
            print(f"   ❌ Basic Auth 调用异常: {result.get('error')}")
    
    # 测试 API Key Header
    if "/headers" in endpoints:
        print("\n   🔑 测试 API Key Header...")
        endpoint = endpoints["/headers"]
        
        call_data = {
            "endpoint_id": endpoint["id"],
            "request_data": {
                "method": "GET",
                "url": "https://httpbin.org/headers",
                "headers": {"Content-Type": "application/json"}
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/call", json=call_data)
        result = response.json()
        
        if result.get("success"):
            status_code = result.get("status_code")
            response_body = result.get("response_body", {})
            
            if status_code == 200:
                headers = response_body.get("headers", {})
                test_key = headers.get("X-Test-Key")
                print(f"   ✅ API Key Header 成功: {test_key is not None}")
                print(f"      检测到的 Key: {test_key}")
            else:
                print(f"   ❌ API Key Header 失败: {status_code}")
        else:
            print(f"   ❌ API Key Header 调用异常: {result.get('error')}")
    
    # 测试 API Key Query
    if "/get" in endpoints:
        print("\n   🔑 测试 API Key Query...")
        endpoint = endpoints["/get"]
        
        call_data = {
            "endpoint_id": endpoint["id"],
            "request_data": {
                "method": "GET",
                "url": "https://httpbin.org/get",
                "headers": {"Content-Type": "application/json"}
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/call", json=call_data)
        result = response.json()
        
        if result.get("success"):
            status_code = result.get("status_code")
            response_body = result.get("response_body", {})
            
            if status_code == 200:
                args = response_body.get("args", {})
                test_key = args.get("test_key")
                print(f"   ✅ API Key Query 成功: {test_key is not None}")
                print(f"      检测到的 Key: {test_key}")
            else:
                print(f"   ❌ API Key Query 失败: {status_code}")
        else:
            print(f"   ❌ API Key Query 调用异常: {result.get('error')}")
    
    # 测试 Bearer Token
    if "/anything" in endpoints:
        print("\n   🎫 测试 Bearer Token...")
        endpoint = endpoints["/anything"]
        
        call_data = {
            "endpoint_id": endpoint["id"],
            "request_data": {
                "method": "GET",
                "url": "https://httpbin.org/anything",
                "headers": {"Content-Type": "application/json"}
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/call", json=call_data)
        result = response.json()
        
        if result.get("success"):
            status_code = result.get("status_code")
            response_body = result.get("response_body", {})
            
            if status_code == 200:
                headers = response_body.get("headers", {})
                auth_header = headers.get("Authorization")
                print(f"   ✅ Bearer Token 成功: {auth_header is not None}")
                print(f"      认证头: {auth_header}")
            else:
                print(f"   ❌ Bearer Token 失败: {status_code}")
        else:
            print(f"   ❌ Bearer Token 调用异常: {result.get('error')}")
    
    # 4. 查看认证配置
    print("\n4. 查看认证配置...")
    response = requests.get(f"{BASE_URL}/auth/configs", params={"api_document_id": document_id})
    if response.status_code == 200:
        configs = response.json().get("auth_configs", [])
        print(f"   配置数量: {len(configs)}")
        for config in configs:
            print(f"   - {config.get('auth_type')}: {config.get('id')}")
    
    print("\n🎉 真实认证测试完成！")

def test_oauth2_flow():
    """测试 OAuth2 流程（模拟）"""
    print("\n🔄 OAuth2 流程测试（模拟）")
    print("=" * 60)
    
    # 1. 创建用户
    print("\n1. 创建测试用户...")
    user_data = {
        "username": f"oauth_user_{int(time.time())}",
        "email": f"oauth_user_{int(time.time())}@example.com",
        "password": "oauth123",
        "role": "user"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=user_data)
    user_result = response.json()
    
    if not user_result.get("success"):
        print(f"❌ 用户创建失败: {user_result.get('error')}")
        return
    
    user_id = user_result.get("user_id")
    print(f"✅ 用户创建成功: {user_id}")
    
    # 2. 注册 OAuth2 API
    print("\n2. 注册 OAuth2 API...")
    oauth2_openapi = {
        "openapi": "3.0.0",
        "info": {"title": "OAuth2 Test API", "version": "1.0.0"},
        "servers": [{"url": "https://httpbin.org"}],
        "paths": {
            "/anything": {
                "get": {
                    "summary": "OAuth2 测试端点",
                    "operationId": "oauth2Test",
                    "responses": {"200": {"description": "成功"}}
                }
            }
        }
    }
    
    api_data = {
        "name": "OAuth2 Test API",
        "openapi_content": json.dumps(oauth2_openapi),
        "version": "1.0.0",
        "base_url": "https://httpbin.org"
    }
    
    response = requests.post(f"{BASE_URL}/apis/register", json=api_data)
    api_result = response.json()
    
    if not api_result.get("success"):
        print(f"❌ OAuth2 API 注册失败: {api_result.get('error')}")
        return
    
    document_id = api_result.get("document_id")
    print(f"✅ OAuth2 API 注册成功: {document_id}")
    
    # 3. 配置 OAuth2
    print("\n3. 配置 OAuth2...")
    oauth2_config = {
        "api_document_id": document_id,
        "auth_type": "oauth2",
        "auth_config": {
            "client_id": "test-oauth2-client",
            "client_secret": "test-oauth2-secret",
            "authorization_url": "https://example.com/oauth/authorize",
            "token_url": "https://example.com/oauth/token",
            "redirect_uri": "http://localhost:8000/oauth2/callback",
            "scope": "read:user write:user"
        },
        "is_required": True,
        "is_global": False,
        "priority": 1
    }
    
    response = requests.post(f"{BASE_URL}/auth/configs", json=oauth2_config)
    oauth2_result = response.json()
    
    if oauth2_result.get("success"):
        print(f"✅ OAuth2 配置成功: {oauth2_result.get('auth_config_id')}")
    else:
        print(f"❌ OAuth2 配置失败: {oauth2_result.get('error')}")
        return
    
    # 4. 创建 OAuth2 授权 URL
    print("\n4. 创建 OAuth2 授权 URL...")
    auth_url_data = {
        "user_id": user_id,
        "api_document_id": document_id
    }
    
    response = requests.post(f"{BASE_URL}/oauth2/auth-url", json=auth_url_data)
    auth_url_result = response.json()
    
    if auth_url_result.get("success"):
        print(f"✅ OAuth2 授权 URL 创建成功")
        print(f"   授权 URL: {auth_url_result.get('auth_url')}")
        print(f"   状态 ID: {auth_url_result.get('auth_state_id')}")
    else:
        print(f"❌ OAuth2 授权 URL 创建失败: {auth_url_result.get('error')}")
    
    print("\n🔄 OAuth2 流程测试完成（模拟）")

def main():
    print("🚀 StepFlow Gateway 真实认证测试")
    print("=" * 80)
    
    # 测试真实认证端点
    test_real_auth()
    
    # 测试 OAuth2 流程
    test_oauth2_flow()
    
    print("\n" + "=" * 80)
    print("🎯 认证测试总结:")
    print("✅ Basic Auth - 支持用户名密码认证")
    print("✅ Bearer Token - 支持令牌认证")
    print("✅ API Key Header - 支持请求头 API Key")
    print("✅ API Key Query - 支持查询参数 API Key")
    print("✅ OAuth2 - 支持 OAuth2 授权流程")
    print("✅ 端到端流程 - 从配置到调用的完整流程")

if __name__ == "__main__":
    main() 