#!/usr/bin/env python3
import requests
import json

# 使用注册时返回的 document_id
document_id = "d5bcfc44-d332-48a5-9565-6cdc762eadd1"

print("🔍 调试 Flutter 端路径参数问题")
print("=" * 60)

# 问题 1: Flutter 可能没有传递 path_params
print("1. 测试没有传递 path_params 的情况...")
try:
    response = requests.post(
        "http://localhost:8000/api/call/path",
        params={
            "path": "/pet/{petId}",
            "method": "GET",
            "api_document_id": document_id
        },
        json={}  # 空的请求体
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   URL: {result.get('url')}")
        print(f"   成功: {result.get('success')}")
        if not result.get('success'):
            print(f"   错误: {result.get('error')}")
    else:
        print(f"   响应: {response.text}")
        
except Exception as e:
    print(f"   ❌ 异常: {e}")

# 问题 2: Flutter 可能传递了错误的参数名
print("\n2. 测试错误的参数名...")
try:
    response = requests.post(
        "http://localhost:8000/api/call/path",
        params={
            "path": "/pet/{petId}",
            "method": "GET",
            "api_document_id": document_id
        },
        json={
            "params": {"petId": "1"}  # 使用 params 而不是 path_params
        }
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   URL: {result.get('url')}")
        print(f"   成功: {result.get('success')}")
        if not result.get('success'):
            print(f"   错误: {result.get('error')}")
    else:
        print(f"   响应: {response.text}")
        
except Exception as e:
    print(f"   ❌ 异常: {e}")

# 问题 3: Flutter 可能传递了错误的参数值类型
print("\n3. 测试错误的参数值类型...")
try:
    response = requests.post(
        "http://localhost:8000/api/call/path",
        params={
            "path": "/pet/{petId}",
            "method": "GET",
            "api_document_id": document_id
        },
        json={
            "path_params": {"petId": 1}  # 数字而不是字符串
        }
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   URL: {result.get('url')}")
        print(f"   成功: {result.get('success')}")
        if not result.get('success'):
            print(f"   错误: {result.get('error')}")
    else:
        print(f"   响应: {response.text}")
        
except Exception as e:
    print(f"   ❌ 异常: {e}")

# 问题 4: Flutter 可能传递了错误的路径格式
print("\n4. 测试错误的路径格式...")
try:
    response = requests.post(
        "http://localhost:8000/api/call/path",
        params={
            "path": "/pet/{petId}",  # 路径中包含占位符
            "method": "GET",
            "api_document_id": document_id
        },
        json={
            "path_params": {"petId": "1"}
        }
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   URL: {result.get('url')}")
        print(f"   成功: {result.get('success')}")
        if not result.get('success'):
            print(f"   错误: {result.get('error')}")
    else:
        print(f"   响应: {response.text}")
        
except Exception as e:
    print(f"   ❌ 异常: {e}")

# 问题 5: 检查端点匹配逻辑
print("\n5. 检查端点匹配逻辑...")
try:
    # 先获取端点列表
    response = requests.get(f"http://localhost:8000/endpoints?api_document_id={document_id}")
    if response.status_code == 200:
        endpoints = response.json().get('endpoints', [])
        pet_endpoint = next((ep for ep in endpoints if ep['path'] == '/pet/{petId}' and ep['method'] == 'GET'), None)
        if pet_endpoint:
            print(f"   ✅ 找到端点: {pet_endpoint['path']} {pet_endpoint['method']}")
            print(f"   端点 ID: {pet_endpoint['id']}")
        else:
            print(f"   ❌ 未找到端点 /pet/{{petId}} GET")
    else:
        print(f"   ❌ 获取端点失败: {response.text}")
        
except Exception as e:
    print(f"   ❌ 异常: {e}")

print(f"\n{'='*60}")
print("🎯 Flutter 端可能的问题：")
print("1. 没有传递 path_params 参数")
print("2. 使用了错误的参数名（params 而不是 path_params）")
print("3. 参数值类型错误")
print("4. 路径格式错误")
print("5. 端点匹配失败") 