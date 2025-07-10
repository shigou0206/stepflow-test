#!/usr/bin/env python3
import requests
import json

BASE_URL = 'http://localhost:3000'

def test_simple_parse():
    """测试简单的解析请求"""
    print("🔍 测试简单解析...")
    
    # 最简单的OpenAPI文档
    simple_openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": "Simple API",
            "version": "1.0.0"
        },
        "paths": {}
    }
    
    # 测试不同的请求格式
    test_cases = [
        {
            "name": "格式1: content字段 + JSON字符串",
            "payload": {
                "content": json.dumps(simple_openapi)
            }
        },
        {
            "name": "格式2: content字段 + JSON字符串 + content_type",
            "payload": {
                "content": json.dumps(simple_openapi),
                "content_type": "json"
            }
        },
        {
            "name": "格式3: content字段 + JSON字符串 + application/json",
            "payload": {
                "content": json.dumps(simple_openapi),
                "content_type": "application/json"
            }
        },
        {
            "name": "格式4: 直接发送OpenAPI对象",
            "payload": simple_openapi
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/v1/openapi/parse",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    test_simple_parse() 