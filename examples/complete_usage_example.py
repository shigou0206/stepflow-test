#!/usr/bin/env python3
"""
StepFlow Gateway 完整使用示例
演示如何注册 OpenAPI 文档、配置认证、调用 API 的完整流程
"""

import json
import requests
import time
import uuid
from pathlib import Path

# 示例 OpenAPI 文档
PETSTORE_OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "Pet Store API",
        "version": "1.0.0",
        "description": "A sample Pet Store API"
    },
    "servers": [
        {
            "url": "https://petstore.swagger.io/v2",
            "description": "Pet Store API Server"
        }
    ],
    "paths": {
        "/pet/{petId}": {
            "get": {
                "summary": "Find pet by ID",
                "operationId": "getPetById",
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful operation",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                        "status": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/pet": {
            "post": {
                "summary": "Add a new pet",
                "operationId": "addPet",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "status": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Pet added successfully"
                    }
                }
            }
        }
    }
}

def main():
    """主函数：演示 StepFlow Gateway 的完整使用流程"""
    
    # 1. 启动 FastAPI 服务（假设已在运行）
    base_url = "http://localhost:8000"
    
    print("🚀 StepFlow Gateway 完整使用示例")
    print("=" * 60)
    
    # 2. 健康检查
    print("\n1. 健康检查")
    response = requests.get(f"{base_url}/health")
    print(f"   状态: {response.status_code}")
    print(f"   响应: {response.json()}")
    
    # 3. 注册用户（使用随机用户名避免重复）
    print("\n2. 注册用户")
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "password123",
        "role": "user"
    }
    response = requests.post(f"{base_url}/register", json=user_data)
    print(f"   状态: {response.status_code}")
    register_result = response.json()
    print(f"   响应: {register_result}")
    
    # 4. 用户登录
    print("\n3. 用户登录")
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = requests.post(f"{base_url}/login", json=login_data)
    print(f"   状态: {response.status_code}")
    login_result = response.json()
    print(f"   响应: {login_result}")
    
    # 5. 注册 OpenAPI 文档
    print("\n4. 注册 OpenAPI 文档")
    register_data = {
        "name": "Pet Store API",
        "openapi_content": json.dumps(PETSTORE_OPENAPI),
        "version": "1.0.0",
        "base_url": "https://petstore.swagger.io/v2"
    }
    response = requests.post(f"{base_url}/apis/register", json=register_data)
    print(f"   状态: {response.status_code}")
    api_result = response.json()
    print(f"   响应: {api_result}")
    
    api_document_id = api_result.get("document_id")
    if not api_document_id:
        print("   ❌ 注册 API 失败，跳过后续步骤")
        return
    
    # 6. 查看注册的 API
    print("\n5. 查看注册的 API")
    response = requests.get(f"{base_url}/apis")
    print(f"   状态: {response.status_code}")
    apis = response.json()
    print(f"   API 列表: {apis}")
    
    # 7. 查看端点
    print("\n6. 查看端点")
    response = requests.get(f"{base_url}/endpoints", params={"api_document_id": api_document_id})
    print(f"   状态: {response.status_code}")
    endpoints = response.json()
    print(f"   端点列表: {endpoints}")
    
    # 8. 配置认证（可选）
    print("\n7. 配置 API Key 认证")
    auth_config = {
        "api_document_id": api_document_id,
        "auth_type": "api_key",
        "auth_config": {
            "key_name": "X-API-Key",
            "key_value": "demo-key-123"
        },
        "is_required": False,
        "priority": 10
    }
    response = requests.post(f"{base_url}/auth/configs", json=auth_config)
    print(f"   状态: {response.status_code}")
    auth_result = response.json()
    print(f"   响应: {auth_result}")
    
    # 9. 调用 API（通过端点 ID）
    print("\n8. 调用 API（通过端点 ID）")
    if endpoints.get("endpoints"):
        endpoint = endpoints["endpoints"][0]  # 使用第一个端点
        endpoint_id = endpoint["id"]
        
        api_call_data = {
            "endpoint_id": endpoint_id,
            "request_data": {
                "method": "GET",
                "url": "https://petstore.swagger.io/v2/pet/1",
                "headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": "demo-key-123"
                },
                "params": {},
                "body": None
            }
        }
        response = requests.post(f"{base_url}/api/call", json=api_call_data)
        print(f"   状态: {response.status_code}")
        call_result = response.json()
        print(f"   API 调用结果: {call_result}")
    
    # 10. 通过路径调用 API
    print("\n9. 通过路径调用 API")
    path_call_data = {
        "method": "GET",
        "url": "https://petstore.swagger.io/v2/pet/1",
        "headers": {
            "Content-Type": "application/json",
            "X-API-Key": "demo-key-123"
        },
        "params": {},
        "body": None
    }
    response = requests.post(
        f"{base_url}/api/call/path?path=/pet/1&method=GET&api_document_id={api_document_id}", 
        json=path_call_data
    )
    print(f"   状态: {response.status_code}")
    path_call_result = response.json()
    print(f"   路径调用结果: {path_call_result}")
    
    # 11. 获取统计信息
    print("\n10. 获取统计信息")
    response = requests.get(f"{base_url}/statistics")
    print(f"   状态: {response.status_code}")
    stats = response.json()
    print(f"   统计信息: {stats}")
    
    # 12. 获取最近的调用日志
    print("\n11. 获取最近的调用日志")
    response = requests.get(f"{base_url}/logs/recent", params={"limit": 5})
    print(f"   状态: {response.status_code}")
    logs = response.json()
    print(f"   最近调用: {logs}")
    
    # 13. 验证会话
    print("\n12. 验证会话")
    if login_result.get("session_token"):
        session_token = login_result["session_token"]
        response = requests.post(f"{base_url}/sessions/validate", json={"session_token": session_token})
        print(f"   状态: {response.status_code}")
        session_result = response.json()
        print(f"   会话验证: {session_result}")
    
    print("\n✅ 完整示例完成！")
    print("\n📖 总结：")
    print("1. ✅ 用户注册和登录")
    print("2. ✅ OpenAPI 文档注册")
    print("3. ✅ 端点管理")
    print("4. ✅ 认证配置")
    print("5. ✅ API 调用")
    print("6. ✅ 监控和日志")
    print("7. ✅ 会话管理")
    
    print("\n🔗 访问地址：")
    print(f"   Swagger 文档: {base_url}/docs")
    print(f"   ReDoc 文档: {base_url}/redoc")
    print(f"   OpenAPI JSON: {base_url}/openapi.json")

def test_oauth2_flow():
    """测试 OAuth2 流程（需要 OAuth2 提供商）"""
    base_url = "http://localhost:8000"
    
    print("\n🔄 OAuth2 流程测试")
    print("=" * 40)
    
    # 1. 创建 OAuth2 认证 URL
    print("1. 创建 OAuth2 认证 URL")
    oauth2_data = {
        "user_id": "test-user-id",
        "api_document_id": "test-api-id"
    }
    response = requests.post(f"{base_url}/oauth2/auth-url", json=oauth2_data)
    print(f"   状态: {response.status_code}")
    oauth2_result = response.json()
    print(f"   响应: {oauth2_result}")
    
    print("\n⚠️  OAuth2 流程需要实际的 OAuth2 提供商支持")

if __name__ == "__main__":
    main()
    # test_oauth2_flow()  # 取消注释测试 OAuth2 