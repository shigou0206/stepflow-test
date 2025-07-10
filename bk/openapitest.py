#!/usr/bin/env python3
"""
StepFlow Gateway OpenAPI API 测试脚本

这个脚本演示了如何使用 StepFlow Gateway 的 OpenAPI 处理 API。
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = 'http://localhost:3000'

def make_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """发送 HTTP 请求"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"不支持的 HTTP 方法: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return None

def test_parse_openapi():
    """测试解析 OpenAPI 文档"""
    print("🔍 测试解析 OpenAPI 文档...")
    
    # 简化的 OpenAPI 文档
    openapi_content = {
        "openapi": "3.0.0",
        "info": {
            "title": "用户管理 API",
            "version": "1.0.0",
            "description": "用户管理相关的 API 接口"
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "获取用户列表",
                    "operationId": "getUsers",
                    "responses": {
                        "200": {
                            "description": "成功获取用户列表",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "创建新用户",
                    "operationId": "createUser",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CreateUserRequest"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "用户创建成功",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "用户ID"},
                        "username": {"type": "string", "description": "用户名"},
                        "email": {"type": "string", "format": "email", "description": "邮箱"},
                        "created_at": {"type": "string", "format": "date-time", "description": "创建时间"}
                    },
                    "required": ["id", "username", "email"]
                },
                "CreateUserRequest": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "用户名"},
                        "email": {"type": "string", "format": "email", "description": "邮箱"},
                        "password": {"type": "string", "description": "密码"}
                    },
                    "required": ["username", "email", "password"]
                }
            }
        }
    }
    
    # 发送原始JSON字符串，不进行额外的JSON转义
    payload = {
        "content": json.dumps(openapi_content),
        "options": {
            "validate": True,
            "generate_dtos": True,
            "resolve_references": True
        }
    }
    
    result = make_request("POST", "/v1/openapi/parse", payload)
    if result and result.get('data'):
        print("✅ 解析成功!")
        print(f"   - API 标题: {result['data']['info']['title']}")
        print(f"   - API 版本: {result['data']['info']['version']}")
        print(f"   - 路径数量: {len(result['data']['paths'])}")
        print(f"   - Schema 数量: {len(result['data']['components']['schemas'])}")
        print(f"   - 验证结果: {'✅ 有效' if result['data']['validation']['is_valid'] else '❌ 无效'}")
        print(f"   - DTO 数量: {len(result['data']['dtos'])}")
        print(f"   - 处理时间: {result['data']['metadata']['processing_time_ms']}ms")
    else:
        print("❌ 解析失败!")
        if result:
            print(f"   响应内容: {result}")
    
    return result

def test_validate_openapi():
    """测试验证 OpenAPI 文档"""
    print("\n🔍 测试验证 OpenAPI 文档...")
    
    # 有效的 OpenAPI 文档
    valid_content = {
        "openapi": "3.0.0",
        "info": {
            "title": "测试 API",
            "version": "1.0.0"
        },
        "paths": {}
    }
    
    payload = {"content": json.dumps(valid_content)}
    result = make_request("POST", "/v1/openapi/validate", payload)
    
    if result and result.get('data'):
        print("✅ 验证成功!")
        print(f"   - 文档有效: {'✅ 是' if result['data']['is_valid'] else '❌ 否'}")
        if result['data']['errors']:
            print(f"   - 错误数量: {len(result['data']['errors'])}")
        if result['data']['warnings']:
            print(f"   - 警告数量: {len(result['data']['warnings'])}")
    else:
        print("❌ 验证失败!")
        if result:
            print(f"   响应内容: {result}")
    
    # 测试无效的 OpenAPI 文档
    print("\n🔍 测试无效的 OpenAPI 文档...")
    invalid_content = {
        "openapi": "3.0.0",
        # 缺少必需的 info 字段
        "paths": {}
    }
    
    payload = {"content": json.dumps(invalid_content)}
    result = make_request("POST", "/v1/openapi/validate", payload)
    
    if result and result.get('data'):
        print("✅ 验证结果:")
        print(f"   - 文档有效: {'✅ 是' if result['data']['is_valid'] else '❌ 否'}")
        if result['data']['errors']:
            print(f"   - 错误: {result['data']['errors']}")
    else:
        print("❌ 验证失败!")
        if result:
            print(f"   响应内容: {result}")
    
    return result

def test_generate_dtos():
    """测试生成 DTO 结构"""
    print("\n🔍 测试生成 DTO 结构...")
    
    openapi_content = {
        "openapi": "3.0.0",
        "info": {
            "title": "DTO 测试 API",
            "version": "1.0.0"
        },
        "paths": {},
        "components": {
            "schemas": {
                "Product": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "price": {"type": "number", "format": "float"},
                        "category": {"type": "string", "enum": ["electronics", "clothing", "books"]},
                        "in_stock": {"type": "boolean"},
                        "tags": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["id", "name", "price"]
                }
            }
        }
    }
    
    payload = {"content": json.dumps(openapi_content)}
    result = make_request("POST", "/v1/openapi/generate-dtos", payload)
    
    if result and result.get('data'):
        print("✅ DTO 生成成功!")
        for dto in result['data']:
            print(f"   - DTO: {dto['name']}")
            for field in dto['fields']:
                # 使用正确的字段名
                field_type = field.get('field_type', 'unknown')
                is_required = field.get('is_required', False)
                required = "✅" if is_required else "❌"
                print(f"     - {field['name']}: {field_type} {required}")
    else:
        print("❌ DTO 生成失败!")
        if result:
            print(f"   响应内容: {result}")
    
    return result

def test_get_schema():
    """测试获取 API Schema"""
    print("\n🔍 测试获取 API Schema...")
    
    result = make_request("GET", "/v1/openapi/schema")
    
    if result and result.get('data'):
        print("✅ Schema 获取成功!")
        schema = result['data']
        print(f"   - OpenAPI 版本: {schema['openapi']}")
        print(f"   - API 标题: {schema['info']['title']}")
        print(f"   - API 版本: {schema['info']['version']}")
        print(f"   - 路径数量: {len(schema['paths'])}")
    else:
        print("❌ Schema 获取失败!")
        if result:
            print(f"   响应内容: {result}")
    
    return result

def main():
    """主函数"""
    print("🚀 StepFlow Gateway OpenAPI API 测试")
    print("=" * 50)
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/v1/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print("❌ 服务器响应异常")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到服务器，请确保 StepFlow Gateway 正在运行")
        print("   启动命令: cd stepflow-gateway && cargo run --bin stepflow-gateway")
        return
    
    # 运行测试
    test_parse_openapi()
    test_validate_openapi()
    test_generate_dtos()
    test_get_schema()
    
    print("\n" + "=" * 50)
    print("🎉 测试完成!")

if __name__ == "__main__":
    main() 