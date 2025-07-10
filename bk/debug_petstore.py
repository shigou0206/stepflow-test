#!/usr/bin/env python3
import requests
import json
import yaml

BASE_URL = 'http://localhost:3000'

def debug_petstore():
    print("🔍 调试 pet_store 解析问题...")
    
    # 方法1: 读取YAML并转换为JSON字符串
    print("\n=== 方法1: YAML -> Python对象 -> JSON字符串 ===")
    with open("templates/pet_store.yml", "r", encoding="utf-8") as f:
        yml_content = yaml.safe_load(f)
    
    payload1 = {
        "content": json.dumps(yml_content, ensure_ascii=False)
    }
    
    print(f"Payload1 类型: {type(payload1['content'])}")
    print(f"Payload1 前100字符: {payload1['content'][:100]}")
    
    response1 = requests.post(
        f"{BASE_URL}/v1/openapi/parse",
        json=payload1,
        headers={"Content-Type": "application/json"}
    )
    print(f"方法1 状态码: {response1.status_code}")
    print(f"方法1 响应: {response1.text}")
    
    # 方法2: 直接读取原始YAML字符串
    print("\n=== 方法2: 原始YAML字符串 ===")
    with open("templates/pet_store.yml", "r", encoding="utf-8") as f:
        yml_raw = f.read()
    
    payload2 = {
        "content": yml_raw
    }
    
    print(f"Payload2 类型: {type(payload2['content'])}")
    print(f"Payload2 前100字符: {payload2['content'][:100]}")
    
    response2 = requests.post(
        f"{BASE_URL}/v1/openapi/parse",
        json=payload2,
        headers={"Content-Type": "application/json"}
    )
    print(f"方法2 状态码: {response2.status_code}")
    print(f"方法2 响应: {response2.text}")
    
    # 方法3: 尝试不同的content_type
    print("\n=== 方法3: 添加content_type字段 ===")
    payload3 = {
        "content": json.dumps(yml_content, ensure_ascii=False),
        "content_type": "json"
    }
    
    response3 = requests.post(
        f"{BASE_URL}/v1/openapi/parse",
        json=payload3,
        headers={"Content-Type": "application/json"}
    )
    print(f"方法3 状态码: {response3.status_code}")
    print(f"方法3 响应: {response3.text}")
    
    # 方法4: 测试最简单的OpenAPI文档
    print("\n=== 方法4: 最简单的OpenAPI文档 ===")
    simple_openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": "Pet Store API",
            "version": "1.0.0"
        },
        "paths": {}
    }
    
    payload4 = {
        "content": json.dumps(simple_openapi)
    }
    
    response4 = requests.post(
        f"{BASE_URL}/v1/openapi/parse",
        json=payload4,
        headers={"Content-Type": "application/json"}
    )
    print(f"方法4 状态码: {response4.status_code}")
    print(f"方法4 响应: {response4.text}")

if __name__ == "__main__":
    debug_petstore() 