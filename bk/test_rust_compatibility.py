#!/usr/bin/env python3
import requests
import json

BASE_URL = 'http://localhost:3000'

def test_rust_compatibility():
    print("🔍 测试与 Rust 测试相同的 JSON 内容...")
    
    # 使用与 Rust 测试完全相同的 JSON 内容
    schema_with_ref = {
        "openapi": "3.0.0",
        "info": {
            "title": "测试 API",
            "version": "1.0.0"
        },
        "paths": {},
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "category": {"$ref": "#/components/schemas/Category"}
                    }
                },
                "Category": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    }
                }
            }
        }
    }
    
    print("  测试包含 $ref 引用的 schema 解析...")
    
    # 测试方法1: 直接发送 JSON 对象（应该失败）
    print("\n=== 方法1: 直接发送 JSON 对象 ===")
    try:
        response1 = requests.post(
            f"{BASE_URL}/v1/openapi/parse",
            json=schema_with_ref,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response1.status_code}")
        print(f"响应: {response1.text}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 测试方法2: 使用 content 字段包装 JSON 字符串
    print("\n=== 方法2: 使用 content 字段包装 JSON 字符串 ===")
    payload = {
        "content": json.dumps(schema_with_ref, ensure_ascii=False)
    }
    
    try:
        response2 = requests.post(
            f"{BASE_URL}/v1/openapi/parse",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response2.status_code}")
        print(f"响应: {response2.text}")
        
        if response2.status_code == 200:
            result = response2.json()
            if result.get('success'):
                print("✅ HTTP API 解析成功!")
                data = result.get('data', {})
                if 'components' in data and 'schemas' in data['components']:
                    print(f"   - Schema 数量: {len(data['components']['schemas'])}")
                    if 'Pet' in data['components']['schemas']:
                        print("   - Pet schema 存在")
                    if 'Category' in data['components']['schemas']:
                        print("   - Category schema 存在")
            else:
                print(f"❌ HTTP API 解析失败: {result.get('error')}")
        else:
            print(f"❌ HTTP 请求失败: {response2.text}")
            
    except Exception as e:
        print(f"错误: {e}")
    
    # 测试方法3: 使用 content 字段包装原始 JSON 字符串
    print("\n=== 方法3: 使用 content 字段包装原始 JSON 字符串 ===")
    raw_json = '''{
  "openapi": "3.0.0",
  "info": {
    "title": "测试 API",
    "version": "1.0.0"
  },
  "paths": {},
  "components": {
    "schemas": {
      "Pet": {
        "type": "object",
        "properties": {
          "id": {"type": "integer"},
          "name": {"type": "string"},
          "category": {"$ref": "#/components/schemas/Category"}
        }
      },
      "Category": {
        "type": "object",
        "properties": {
          "id": {"type": "integer"},
          "name": {"type": "string"}
        }
      }
    }
  }
}'''
    
    payload3 = {
        "content": raw_json
    }
    
    try:
        response3 = requests.post(
            f"{BASE_URL}/v1/openapi/parse",
            json=payload3,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response3.status_code}")
        print(f"响应: {response3.text}")
        
        if response3.status_code == 200:
            result = response3.json()
            if result.get('success'):
                print("✅ HTTP API 解析成功!")
            else:
                print(f"❌ HTTP API 解析失败: {result.get('error')}")
        else:
            print(f"❌ HTTP 请求失败: {response3.text}")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_rust_compatibility() 