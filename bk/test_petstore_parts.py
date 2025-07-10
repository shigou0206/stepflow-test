#!/usr/bin/env python3
import requests
import json
import yaml

BASE_URL = 'http://localhost:3000'

def test_petstore_parts():
    print("🔍 逐步测试 pet_store 文档的不同部分...")
    
    with open("templates/pet_store.yml", "r", encoding="utf-8") as f:
        full_content = yaml.safe_load(f)
    
    # 测试1: 基础结构
    print("\n=== 测试1: 基础结构 ===")
    basic = {
        "openapi": full_content["openapi"],
        "info": full_content["info"],
        "paths": {}
    }
    
    payload = {"content": json.dumps(basic)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"基础结构: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")
    
    # 测试2: 添加servers
    print("\n=== 测试2: 添加servers ===")
    with_servers = basic.copy()
    with_servers["servers"] = full_content["servers"]
    
    payload = {"content": json.dumps(with_servers)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"添加servers: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")
    
    # 测试3: 添加externalDocs
    print("\n=== 测试3: 添加externalDocs ===")
    with_external = with_servers.copy()
    with_external["externalDocs"] = full_content["externalDocs"]
    
    payload = {"content": json.dumps(with_external)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"添加externalDocs: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")
    
    # 测试4: 添加tags
    print("\n=== 测试4: 添加tags ===")
    with_tags = with_external.copy()
    with_tags["tags"] = full_content["tags"]
    
    payload = {"content": json.dumps(with_tags)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"添加tags: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")
    
    # 测试5: 添加简单路径
    print("\n=== 测试5: 添加简单路径 ===")
    with_simple_paths = with_tags.copy()
    # 只添加一个最简单的路径
    simple_path = {
        "/test": {
            "get": {
                "summary": "Test endpoint",
                "responses": {
                    "200": {"description": "OK"}
                }
            }
        }
    }
    with_simple_paths["paths"] = simple_path
    
    payload = {"content": json.dumps(with_simple_paths)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"添加简单路径: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")
    
    # 测试6: 添加components
    print("\n=== 测试6: 添加components ===")
    with_components = with_simple_paths.copy()
    with_components["components"] = full_content["components"]
    
    payload = {"content": json.dumps(with_components)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"添加components: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")
    
    # 测试7: 添加完整路径
    print("\n=== 测试7: 添加完整路径 ===")
    with_full_paths = with_components.copy()
    with_full_paths["paths"] = full_content["paths"]
    
    payload = {"content": json.dumps(with_full_paths)}
    response = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload)
    print(f"添加完整路径: {'✅ 成功' if response.json().get('success') else '❌ 失败'}")

if __name__ == "__main__":
    test_petstore_parts() 