#!/usr/bin/env python3
import json
import requests

# 读取 Petstore OpenAPI 文档
with open('templates/pet_store.json', 'r') as f:
    openapi_content = json.load(f)

# 注册 API
response = requests.post(
    "http://localhost:8000/apis/register",
    json={
        "name": "Petstore API v3",
        "openapi_content": json.dumps(openapi_content)
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    print("✅ Petstore API 注册成功!")
else:
    print("❌ 注册失败") 