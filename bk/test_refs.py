#!/usr/bin/env python3
import requests
import json

BASE_URL = 'http://localhost:3000'

def test_refs_parse():
    """测试包含$ref引用的解析请求"""
    print("🔍 测试$ref引用解析...")
    
    # 测试包含$ref的OpenAPI文档
    openapi_with_refs = {
        "openapi": "3.0.0",
        "info": {
            "title": "用户管理 API",
            "version": "1.0.0"
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "获取用户列表",
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
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                        "email": {"type": "string"}
                    }
                }
            }
        }
    }
    
    try:
        payload = {
            "content": json.dumps(openapi_with_refs)
        }
        response = requests.post(
            f"{BASE_URL}/v1/openapi/parse",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 成功!")
                data = result.get('data', {})
                print(f"   - Schema数量: {len(data.get('components', {}).get('schemas', {}))}")
            else:
                print(f"❌ 失败: {result.get('error')}")
        else:
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_refs_parse() 