#!/usr/bin/env python3
"""
调试 Flutter 端调用 /api/call/path 接口的问题
模拟 Flutter 的请求格式，查看具体的错误信息
"""

import json
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_flutter_api_call():
    """测试 Flutter 端可能的调用方式"""
    
    print("🔍 调试 Flutter API 调用问题")
    print("=" * 60)
    
    # 1. 获取可用的 API 列表
    print("\n1. 获取 API 列表...")
    try:
        response = requests.get(f"{BASE_URL}/apis")
        if response.status_code == 200:
            apis = response.json()
            print(f"✅ 找到 {len(apis.get('apis', []))} 个 API")
            
            # 选择第一个 API 进行测试
            if apis.get('apis'):
                test_api = apis['apis'][0]
                api_document_id = test_api['id']
                print(f"   使用 API: {test_api['name']} (ID: {api_document_id})")
            else:
                print("❌ 没有可用的 API")
                return
        else:
            print(f"❌ 获取 API 列表失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 获取 API 列表异常: {e}")
        return
    
    # 2. 获取端点列表
    print("\n2. 获取端点列表...")
    try:
        response = requests.get(f"{BASE_URL}/endpoints", params={"api_document_id": api_document_id})
        if response.status_code == 200:
            endpoints = response.json()
            print(f"✅ 找到 {len(endpoints.get('endpoints', []))} 个端点")
            
            # 选择一个简单的 GET 端点进行测试
            test_endpoint = None
            for endpoint in endpoints.get('endpoints', []):
                if endpoint['method'] == 'GET' and not '{' in endpoint['path']:
                    test_endpoint = endpoint
                    break
            
            if test_endpoint:
                print(f"   使用端点: {test_endpoint['method']} {test_endpoint['path']}")
            else:
                print("❌ 没有找到合适的测试端点")
                return
        else:
            print(f"❌ 获取端点列表失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 获取端点列表异常: {e}")
        return
    
    # 3. 测试不同的请求格式
    print("\n3. 测试不同的请求格式...")
    
    # 格式 1: 最简单的请求
    print("\n   格式 1: 最简单的请求")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        # 空的请求体
        request_data = {}
        
        response = requests.post(url, params=params, json=request_data)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 成功: {result.get('success')}")
            if not result.get('success'):
                print(f"   错误: {result.get('error')}")
        else:
            print(f"   ❌ 失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 格式 2: 带 headers 的请求
    print("\n   格式 2: 带 headers 的请求")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        request_data = {
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        }
        
        response = requests.post(url, params=params, json=request_data)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 成功: {result.get('success')}")
            if not result.get('success'):
                print(f"   错误: {result.get('error')}")
        else:
            print(f"   ❌ 失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 格式 3: 完整的请求数据
    print("\n   格式 3: 完整的请求数据")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        request_data = {
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "params": {},
            "body": None,
            "client_ip": "127.0.0.1",
            "user_agent": "Flutter/1.0"
        }
        
        response = requests.post(url, params=params, json=request_data)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 成功: {result.get('success')}")
            if not result.get('success'):
                print(f"   错误: {result.get('error')}")
        else:
            print(f"   ❌ 失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 格式 4: 模拟 Flutter 可能的错误格式
    print("\n   格式 4: 模拟可能的错误格式")
    
    # 4a: 缺少必需参数
    print("\n   4a: 缺少 path 参数")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        request_data = {}
        
        response = requests.post(url, params=params, json=request_data)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 4b: 缺少 method 参数
    print("\n   4b: 缺少 method 参数")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "api_document_id": api_document_id
        }
        
        request_data = {}
        
        response = requests.post(url, params=params, json=request_data)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 4c: 错误的 JSON 格式
    print("\n   4c: 错误的 JSON 格式")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        # 发送非 JSON 数据
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, params=params, data="invalid json", headers=headers)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 4d: 错误的 Content-Type
    print("\n   4d: 错误的 Content-Type")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": test_endpoint['path'],
            "method": test_endpoint['method'],
            "api_document_id": api_document_id
        }
        
        # 使用错误的 Content-Type
        headers = {"Content-Type": "text/plain"}
        response = requests.post(url, params=params, json=request_data, headers=headers)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 调试完成")
    print("\n💡 建议：")
    print("1. 检查 Flutter 端是否正确设置了 Content-Type: application/json")
    print("2. 检查请求体是否是有效的 JSON 格式")
    print("3. 确保所有必需的查询参数都已提供")
    print("4. 检查 api_document_id 是否存在且有效")

if __name__ == "__main__":
    test_flutter_api_call() 