#!/usr/bin/env python3
import requests
import json

BASE_URL = 'http://localhost:3000'

def test_complex_parse():
    """测试复杂的解析请求"""
    print("🔍 测试复杂解析...")
    
    # 逐步构建复杂的OpenAPI文档
    test_cases = [
        {
            "name": "基础文档",
            "content": {
                "openapi": "3.0.0",
                "info": {
                    "title": "用户管理 API",
                    "version": "1.0.0"
                },
                "paths": {}
            }
        },
        {
            "name": "添加servers",
            "content": {
                "openapi": "3.0.0",
                "info": {
                    "title": "用户管理 API",
                    "version": "1.0.0"
                },
                "servers": [
                    {"url": "https://api.example.com/v1"}
                ],
                "paths": {}
            }
        },
        {
            "name": "添加简单路径",
            "content": {
                "openapi": "3.0.0",
                "info": {
                    "title": "用户管理 API",
                    "version": "1.0.0"
                },
                "servers": [
                    {"url": "https://api.example.com/v1"}
                ],
                "paths": {
                    "/users": {
                        "get": {
                            "summary": "获取用户列表",
                            "responses": {
                                "200": {
                                    "description": "成功"
                                }
                            }
                        }
                    }
                }
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        try:
            payload = {
                "content": json.dumps(test_case['content'])
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
                else:
                    print(f"❌ 失败: {result.get('error')}")
            else:
                print(f"响应: {response.text}")
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    test_complex_parse() 