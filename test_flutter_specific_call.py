#!/usr/bin/env python3
import requests
import json

# 使用注册时返回的 document_id
document_id = "d5bcfc44-d332-48a5-9565-6cdc762eadd1"

print("🔍 测试 Flutter 端特定调用格式")
print("=" * 60)

# 模拟 Flutter 端的实际调用
print("1. 模拟 Flutter 端调用（传递 /pet/{petId} 路径）...")

# Flutter 端可能的调用格式
flutter_calls = [
    {
        "name": "Flutter 标准格式",
        "params": {
            "path": "/pet/{petId}",
            "method": "GET",
            "api_document_id": document_id
        },
        "json": {
            "path_params": {"petId": "1"},
            "headers": {"Accept": "application/json"}
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
        "name": "Flutter 使用 params 而不是 path_params",
        "params": {
            "path": "/pet/{petId}",
            "method": "GET",
            "api_document_id": document_id
        },
        "json": {
            "params": {"petId": "1"}
        }
    }
]

for i, call in enumerate(flutter_calls, 1):
    print(f"\n{i}. {call['name']}...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/call/path",
            params=call["params"],
            json=call["json"]
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   成功: {result.get('success')}")
            print(f"   目标 URL: {result.get('url')}")
            print(f"   响应状态: {result.get('status_code')}")
            
            if result.get('success'):
                if result.get('status_code') == 200:
                    print(f"   ✅ API 调用成功")
                    if isinstance(result.get('response_body'), dict):
                        pet = result['response_body']
                        print(f"   Pet ID: {pet.get('id')}")
                        print(f"   Pet Name: {pet.get('name')}")
                        print(f"   Pet Status: {pet.get('status')}")
                else:
                    print(f"   ⚠️  API 返回错误状态: {result.get('status_code')}")
                    if result.get('response_body'):
                        print(f"   错误信息: {result.get('response_body')}")
            else:
                print(f"   ❌ 调用失败: {result.get('error')}")
        else:
            print(f"   ❌ HTTP 错误: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")

print(f"\n{'='*60}")
print("🎯 Flutter 端调用建议：")
print("✅ 使用 path_params 传递路径参数")
print("✅ 确保路径参数值正确（字符串格式）")
print("✅ 检查 API 文档 ID 是否正确")
print("✅ 确保端点路径格式正确") 