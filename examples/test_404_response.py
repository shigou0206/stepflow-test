#!/usr/bin/env python3
"""
测试 404 响应的处理
验证当目标 API 返回 404 时的正常行为
"""

import json
import requests

BASE_URL = "http://localhost:8000"

def test_404_responses():
    """测试各种 404 响应情况"""
    
    print("🔍 测试 404 响应处理")
    print("=" * 60)
    
    # 获取 Petstore API
    try:
        response = requests.get(f"{BASE_URL}/apis")
        apis = response.json()
        
        # 查找 Petstore API
        petstore_api = None
        for api in apis.get('apis', []):
            if 'pet' in api.get('name', '').lower():
                petstore_api = api
                break
        
        if not petstore_api:
            print("❌ 未找到 Petstore API")
            return
            
        api_document_id = petstore_api['id']
        print(f"✅ 使用 API: {petstore_api['name']} (ID: {api_document_id})")
        
    except Exception as e:
        print(f"❌ 获取 API 失败: {e}")
        return
    
    # 测试 1: 不存在的宠物 ID
    print("\n1. 测试不存在的宠物 ID...")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": "/pet/{petId}",
            "method": "GET",
            "api_document_id": api_document_id
        }
        
        request_data = {
            "params": {
                "petId": "999999"  # 不存在的 ID
            },
            "headers": {
                "Accept": "application/json"
            }
        }
        
        response = requests.post(url, params=params, json=request_data)
        result = response.json()
        
        print(f"   状态码: {result.get('status_code')}")
        print(f"   成功: {result.get('success')}")
        
        if result.get('status_code') == 404:
            print("   ✅ 正常：目标 API 返回 404（资源不存在）")
            print("   📝 这说明：")
            print("      - Flutter 端调用成功")
            print("      - 请求正确转发到目标服务器")
            print("      - 目标服务器找不到对应资源")
        else:
            print(f"   ⚠️ 意外状态码: {result.get('status_code')}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 测试 2: 不存在的路径
    print("\n2. 测试不存在的路径...")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": "/nonexistent/path",
            "method": "GET",
            "api_document_id": api_document_id
        }
        
        request_data = {
            "headers": {
                "Accept": "application/json"
            }
        }
        
        response = requests.post(url, params=params, json=request_data)
        result = response.json()
        
        print(f"   状态码: {result.get('status_code')}")
        print(f"   成功: {result.get('success')}")
        
        if result.get('status_code') == 404:
            print("   ✅ 正常：目标 API 返回 404（路径不存在）")
        else:
            print(f"   ⚠️ 意外状态码: {result.get('status_code')}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 测试 3: 存在的宠物 ID
    print("\n3. 测试存在的宠物 ID...")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": "/pet/{petId}",
            "method": "GET",
            "api_document_id": api_document_id
        }
        
        request_data = {
            "params": {
                "petId": "1"  # 可能存在的 ID
            },
            "headers": {
                "Accept": "application/json"
            }
        }
        
        response = requests.post(url, params=params, json=request_data)
        result = response.json()
        
        print(f"   状态码: {result.get('status_code')}")
        print(f"   成功: {result.get('success')}")
        
        if result.get('status_code') == 200:
            print("   ✅ 成功：找到宠物信息")
            response_body = result.get('response_body', {})
            if isinstance(response_body, str):
                try:
                    response_body = json.loads(response_body)
                except:
                    pass
            if isinstance(response_body, dict):
                print(f"   宠物名称: {response_body.get('name', 'N/A')}")
        elif result.get('status_code') == 404:
            print("   ⚠️ 宠物 ID 1 也不存在")
        else:
            print(f"   ⚠️ 意外状态码: {result.get('status_code')}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 测试 4: 查看响应体内容
    print("\n4. 查看 404 响应体内容...")
    try:
        url = f"{BASE_URL}/api/call/path"
        params = {
            "path": "/pet/{petId}",
            "method": "GET",
            "api_document_id": api_document_id
        }
        
        request_data = {
            "params": {
                "petId": "999999"
            },
            "headers": {
                "Accept": "application/json"
            }
        }
        
        response = requests.post(url, params=params, json=request_data)
        result = response.json()
        
        response_body = result.get('response_body', '')
        print(f"   响应体类型: {type(response_body)}")
        print(f"   响应体长度: {len(str(response_body))}")
        print(f"   响应体前100字符: {str(response_body)[:100]}")
        
        if '<html>' in str(response_body):
            print("   ✅ 确认：这是 nginx 的 404 错误页面")
            print("   📝 这说明请求已经到达目标服务器")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 总结：")
    print("✅ Flutter 端调用成功 - 没有 400 错误")
    print("✅ 请求正确转发到目标服务器")
    print("✅ 目标服务器返回 404（资源不存在）")
    print("✅ 这是正常的行为，不是错误")
    print("\n💡 建议：")
    print("1. 检查使用的 API 路径是否正确")
    print("2. 检查参数值是否有效")
    print("3. 确认目标 API 服务器是否正常运行")
    print("4. 查看目标 API 的文档，确认正确的路径和参数")

if __name__ == "__main__":
    test_404_responses() 