#!/usr/bin/env python3
import requests
import json
import yaml

BASE_URL = 'http://localhost:3000'

def test_components_parts():
    print("🔍 测试 components 中的不同子字段...")
    
    with open("templates/pet_store.yml", "r", encoding="utf-8") as f:
        full_content = yaml.safe_load(f)
    
    # 基础结构（已知可以工作）
    base = {
        "openapi": full_content["openapi"],
        "info": full_content["info"],
        "paths": {}
    }
    
    components = full_content["components"]
    
    # 测试每个子字段
    print("\n=== 测试 components 子字段 ===")
    
    # 测试 schemas
    print("测试 schemas...")
    test_doc = base.copy()
    test_doc["components"] = {"schemas": components["schemas"]}
    
    payload = {"content": json.dumps(test_doc)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"schemas: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")
    
    # 测试 requestBodies
    print("测试 requestBodies...")
    test_doc = base.copy()
    test_doc["components"] = {"requestBodies": components["requestBodies"]}
    
    payload = {"content": json.dumps(test_doc)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"requestBodies: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")
    
    # 测试 securitySchemes
    print("测试 securitySchemes...")
    test_doc = base.copy()
    test_doc["components"] = {"securitySchemes": components["securitySchemes"]}
    
    payload = {"content": json.dumps(test_doc)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"securitySchemes: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")
    
    # 测试完整的components
    print("测试完整components...")
    test_doc = base.copy()
    test_doc["components"] = components
    
    payload = {"content": json.dumps(test_doc)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"完整components: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")

if __name__ == "__main__":
    test_components_parts() 