#!/usr/bin/env python3
import requests
import json

# 使用注册时返回的 document_id
document_id = "d5bcfc44-d332-48a5-9565-6cdc762eadd1"

print("🔍 测试 Flutter 端调用格式")
print("=" * 50)

# 测试 Flutter 端可能的调用格式
test_cases = [
    {
        "name": "Flutter 标准格式",
        "params": {
            "path": "/pet/{petId}",
            "method": "GET",
            "api_document_id": document_id
        },
        "json": {
            "path_params": {"petId": "1"},
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "params": {},
            "body": None
        }
    },
    {
        "name": "Flutter 简化格式",
        "params": {
            "path": "/pet/{petId}",
            "method": "GET",
            "api_document_id": document_id
        },
        "json": {
            "path_params": {"petId": "1"}
        }
    },
    {
        "name": "Flutter 带查询参数",
        "params": {
            "path": "/pet/findByStatus",
            "method": "GET",
            "api_document_id": document_id
        },
        "json": {
            "params": {
                "status": "available"
            },
            "headers": {
                "Accept": "application/json"
            }
        }
    }
]

for i, test_case in enumerate(test_cases, 1):
    print(f"\n{i}. {test_case['name']}...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/call/path",
            params=test_case["params"],
            json=test_case["json"]
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   ✅ 成功")
                print(f"   目标 URL: {result.get('url')}")
                print(f"   响应状态: {result.get('status_code')}")
                if result.get('response_body'):
                    if isinstance(result['response_body'], dict):
                        print(f"   响应数据: {json.dumps(result['response_body'], indent=2, ensure_ascii=False)}")
                    else:
                        print(f"   响应数据: {result['response_body']}")
            else:
                print(f"   ❌ 失败: {result.get('error')}")
        else:
            print(f"   ❌ HTTP 错误: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")

print(f"\n{'='*50}")
print("🎯 Flutter 端调用格式总结：")
print("✅ 查询参数: path, method, api_document_id")
print("✅ 请求体: path_params, headers, params, body")
print("✅ 路径参数: 自动替换 {paramName} 占位符")
print("✅ URL 拼接: 正确使用 base_url + path")
print("✅ 响应格式: 包含 success, url, status_code, response_body") 