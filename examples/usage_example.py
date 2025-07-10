#!/usr/bin/env python3
"""
StepFlow Gateway 使用示例
演示如何注册 OpenAPI 文档、配置认证、调用 API
"""

import json
import requests
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
    
    print("🚀 StepFlow Gateway 使用示例")
    print("=" * 50)
    
    # 2. 健康检查
    print("\n1. 健康检查")
    response = requests.get(f"{base_url}/health")
    print(f"   状态: {response.status_code}")
    print(f"   响应: {response.json()}")
    
    # 3. 注册用户
    print("\n2. 注册用户")
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "role": "user"
    }
    response = requests.post(f"{base_url}/register", json=user_data)
    print(f"   状态: {response.status_code}")
    print(f"   响应: {response.json()}")
    
    # 4. 用户登录
    print("\n3. 用户登录")
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    response = requests.post(f"{base_url}/login", json=login_data)
    print(f"   状态: {response.status_code}")
    login_result = response.json()
    print(f"   响应: {login_result}")
    
    # 5. 注册 OpenAPI 文档（通过 HTTP API）
    print("\n4. 注册 OpenAPI 文档")
    # 注意：这里需要扩展 FastAPI 接口来支持 OpenAPI 注册
    # 暂时跳过，直接演示 API 调用
    
    # 6. 演示 API 调用（模拟）
    print("\n5. API 调用示例")
    print("   注意：需要先注册 OpenAPI 文档才能调用具体 API")
    print("   这里展示调用格式：")
    
    api_call_example = {
        "endpoint_id": "pet-get-1",  # 需要先注册 OpenAPI 文档获得
        "request_data": {
            "method": "GET",
            "url": "https://petstore.swagger.io/v2/pet/1",
            "headers": {
                "Content-Type": "application/json"
            },
            "params": {},
            "body": None
        }
    }
    print(f"   请求格式: {json.dumps(api_call_example, indent=2)}")
    
    # 7. 获取统计信息
    print("\n6. 获取统计信息")
    response = requests.get(f"{base_url}/statistics")
    print(f"   状态: {response.status_code}")
    print(f"   响应: {response.json()}")
    
    print("\n✅ 示例完成！")
    print("\n📖 下一步：")
    print("1. 访问 http://localhost:8000/docs 查看 Swagger 文档")
    print("2. 扩展 FastAPI 接口支持 OpenAPI 文档注册")
    print("3. 配置认证和 API 调用")

def register_openapi_via_http():
    """通过 HTTP API 注册 OpenAPI 文档（需要扩展接口）"""
    base_url = "http://localhost:8000"
    
    # 这个接口需要扩展 FastAPI 服务来支持
    register_data = {
        "name": "Pet Store API",
        "openapi_content": json.dumps(PETSTORE_OPENAPI),
        "version": "1.0.0",
        "base_url": "https://petstore.swagger.io/v2"
    }
    
    # 假设有这个接口
    # response = requests.post(f"{base_url}/apis/register", json=register_data)
    # return response.json()
    
    print("⚠️  需要扩展 FastAPI 接口来支持 OpenAPI 注册")

if __name__ == "__main__":
    main()