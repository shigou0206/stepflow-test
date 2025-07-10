#!/usr/bin/env python3
"""
测试 Petstore API 的有效端点
找出哪些端点能正常返回数据
"""

import json
import requests

BASE_URL = "http://localhost:8000"

def test_valid_endpoints():
    """测试 Petstore API 的有效端点"""
    
    print("🔍 测试 Petstore API 有效端点")
    print("=" * 60)
    
    # 获取 Petstore API
    try:
        response = requests.get(f"{BASE_URL}/apis")
        apis = response.json()
        
        petstore_api = None
        for api in apis.get('apis', []):
            if 'pet' in api.get('name', '').lower():
                petstore_api = api
                break
        
        if not petstore_api:
            print("❌ 未找到 Petstore API")
            return
            
        api_document_id = petstore_api['id']
        print(f"✅ 使用 API: {petstore_api['name']}")
        print(f"   基础 URL: {petstore_api['base_url']}")
        
    except Exception as e:
        print(f"❌ 获取 API 失败: {e}")
        return
    
    # 测试常用的端点
    test_cases = [
        {
            "name": "查找可用宠物",
            "path": "/pet/findByStatus",
            "method": "GET",
            "params": {"status": "available"},
            "expected_status": 200
        },
        {
            "name": "查找待售宠物",
            "path": "/pet/findByStatus",
            "method": "GET",
            "params": {"status": "pending"},
            "expected_status": 200
        },
        {
            "name": "查找已售宠物",
            "path": "/pet/findByStatus",
            "method": "GET",
            "params": {"status": "sold"},
            "expected_status": 200
        },
        {
            "name": "获取宠物分类",
            "path": "/store/inventory",
            "method": "GET",
            "params": {},
            "expected_status": 200
        },
        {
            "name": "获取用户列表",
            "path": "/user",
            "method": "GET",
            "params": {},
            "expected_status": 200
        },
        {
            "name": "获取订单列表",
            "path": "/store/order",
            "method": "GET",
            "params": {},
            "expected_status": 200
        }
    ]
    
    successful_endpoints = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}...")
        print(f"   路径: {test_case['method']} {test_case['path']}")
        
        try:
            url = f"{BASE_URL}/api/call/path"
            params = {
                "path": test_case['path'],
                "method": test_case['method'],
                "api_document_id": api_document_id
            }
            
            request_data = {
                "params": test_case['params'],
                "headers": {
                    "Accept": "application/json"
                }
            }
            
            response = requests.post(url, params=params, json=request_data)
            result = response.json()
            
            status_code = result.get('status_code')
            success = result.get('success')
            
            print(f"   状态码: {status_code}")
            print(f"   成功: {success}")
            
            if success and status_code == test_case['expected_status']:
                print("   ✅ 端点有效")
                successful_endpoints.append(test_case)
                
                # 显示响应数据摘要
                response_body = result.get('response_body', '')
                if isinstance(response_body, str):
                    try:
                        response_body = json.loads(response_body)
                    except:
                        pass
                
                if isinstance(response_body, list):
                    print(f"   返回 {len(response_body)} 条记录")
                    if response_body:
                        print(f"   第一条: {list(response_body[0].keys())}")
                elif isinstance(response_body, dict):
                    print(f"   返回对象: {list(response_body.keys())}")
                    
            elif success and status_code == 404:
                print("   ⚠️ 端点返回 404（可能不存在）")
            else:
                print(f"   ❌ 端点无效: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 测试结果总结：")
    print(f"✅ 有效端点数量: {len(successful_endpoints)}/{len(test_cases)}")
    
    if successful_endpoints:
        print("\n📋 推荐使用的端点：")
        for endpoint in successful_endpoints:
            print(f"   • {endpoint['method']} {endpoint['path']} - {endpoint['name']}")
        
        print("\n💡 Flutter 端使用示例：")
        if successful_endpoints:
            example = successful_endpoints[0]
            print(f"""
    // 调用 {example['name']}
    final result = await callApiByPath(
      baseUrl: 'http://localhost:8000',
      path: '{example['path']}',
      method: '{example['method']}',
      apiDocumentId: '{api_document_id}',
      requestData: {{
        'params': {example['params']},
        'headers': {{'Accept': 'application/json'}},
      }},
    );
    
    if (result['success'] && result['status_code'] == 200) {{
      // 处理成功响应
      final data = jsonDecode(result['response_body']);
      print('获取到数据: $data');
    }}
            """)
    else:
        print("❌ 没有找到有效的端点")
        print("💡 建议检查 API 文档或联系 API 提供方")

if __name__ == "__main__":
    test_valid_endpoints() 