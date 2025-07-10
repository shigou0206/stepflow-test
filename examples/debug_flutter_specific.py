#!/usr/bin/env python3
"""
专门调试 Flutter 端调用 /api/call/path 接口的问题
检查 Flutter 端可能出现的常见问题
"""

import json
import requests
import urllib.parse

BASE_URL = "http://localhost:8000"

def test_flutter_specific_issues():
    """测试 Flutter 端可能出现的特定问题"""
    
    print("🔍 Flutter 端特定问题调试")
    print("=" * 60)
    
    # 获取测试用的 API 和端点
    try:
        response = requests.get(f"{BASE_URL}/apis")
        apis = response.json()
        test_api = apis['apis'][0]
        api_document_id = test_api['id']
        
        response = requests.get(f"{BASE_URL}/endpoints", params={"api_document_id": api_document_id})
        endpoints = response.json()
        test_endpoint = endpoints['endpoints'][0]
        
        print(f"使用 API: {test_api['name']}")
        print(f"使用端点: {test_endpoint['method']} {test_endpoint['path']}")
        print()
        
    except Exception as e:
        print(f"❌ 获取测试数据失败: {e}")
        return
    
    # 问题 1: Flutter 可能使用错误的 URL 编码
    print("1. 测试 URL 编码问题...")
    
    # 1a: 路径中包含特殊字符
    print("   1a: 路径包含特殊字符")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": "/test/path with spaces",
            "method": "GET",
            "api_document_id": api_document_id
        }
        
        response = requests.post(url, params=params, json={})
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 1b: 参数值包含特殊字符
    print("   1b: 参数值包含特殊字符")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id + " with spaces"
        }
        
        response = requests.post(url, params=params, json={})
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 问题 2: Flutter 可能发送错误的请求体格式
    print("\n2. 测试请求体格式问题...")
    
    # 2a: 请求体为空字符串
    print("   2a: 请求体为空字符串")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, params=params, data="", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 2b: 请求体为 null
    print("   2b: 请求体为 null")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, params=params, data="null", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 2c: 请求体包含 null 值
    print("   2c: 请求体包含 null 值")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        request_data = {
            "headers": None,
            "params": None,
            "body": None
        }
        
        response = requests.post(url, params=params, json=request_data)
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 问题 3: Flutter 可能使用错误的 HTTP 方法
    print("\n3. 测试 HTTP 方法问题...")
    
    # 3a: 使用 GET 而不是 POST
    print("   3a: 使用 GET 而不是 POST")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        response = requests.get(url, params=params)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 问题 4: Flutter 可能发送错误的 Content-Type
    print("\n4. 测试 Content-Type 问题...")
    
    # 4a: 没有设置 Content-Type
    print("   4a: 没有设置 Content-Type")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        response = requests.post(url, params=params, json={})
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 4b: 错误的 Content-Type
    print("   4b: 错误的 Content-Type")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url, params=params, data="test=data", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 问题 5: Flutter 可能发送错误的参数类型
    print("\n5. 测试参数类型问题...")
    
    # 5a: 参数值为数字而不是字符串
    print("   5a: 参数值为数字")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": 123  # 数字而不是字符串
        }
        
        response = requests.post(url, params=params, json={})
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 5b: 参数值为布尔值
    print("   5b: 参数值为布尔值")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": True  # 布尔值
        }
        
        response = requests.post(url, params=params, json={})
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 问题 6: Flutter 可能发送过大的请求体
    print("\n6. 测试请求体大小问题...")
    
    # 6a: 非常大的请求体
    print("   6a: 非常大的请求体")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        # 创建一个很大的请求体
        large_data = {
            "data": "x" * 1000000  # 1MB 的数据
        }
        
        response = requests.post(url, params=params, json=large_data)
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Flutter 特定问题调试完成")
    print("\n💡 Flutter 端检查清单：")
    print("1. ✅ 确保使用 POST 方法")
    print("2. ✅ 设置 Content-Type: application/json")
    print("3. ✅ 确保请求体是有效的 JSON")
    print("4. ✅ 提供所有必需的查询参数 (path, method, api_document_id)")
    print("5. ✅ 参数值应该是字符串类型")
    print("6. ✅ 避免在参数值中使用特殊字符")
    print("7. ✅ 检查请求体大小是否合理")
    print("\n🔧 推荐的 Flutter 调用方式：")
    print("""
    final response = await http.post(
      Uri.parse('$baseUrl/api/call/path?path=${path}&method=${method}&api_document_id=${apiDocumentId}'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'headers': {'Accept': 'application/json'},
        'params': {},
        'body': null,
      }),
    );
    """)

if __name__ == "__main__":
    test_flutter_specific_issues() 