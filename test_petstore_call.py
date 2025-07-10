#!/usr/bin/env python3
import requests
import json

# 使用注册时返回的 document_id
document_id = "d5bcfc44-d332-48a5-9565-6cdc762eadd1"

# 测试调用 /pet/{petId} 端点
response = requests.post(
    "http://localhost:8000/api/call/path",
    params={
        "api_document_id": document_id,
        "path": "/pet/{petId}",
        "method": "GET"
    },
    json={
        "path_params": {"petId": "1"},
        "headers": {},
        "query_params": {},
        "body": None
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    result = response.json()
    if result.get('success'):
        print("✅ Petstore API 调用成功!")
        print(f"目标 URL: {result.get('target_url')}")
        print(f"响应状态: {result.get('response_status')}")
    else:
        print("❌ API 调用失败")
        print(f"错误: {result.get('error')}")
else:
    print("❌ 请求失败") 