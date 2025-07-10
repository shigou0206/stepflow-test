#!/usr/bin/env python3
import requests
import json

BASE_URL = 'http://localhost:3000'

def debug_dto_structure():
    print("🔍 调试 DTO 结构...")
    
    openapi_content = {
        "openapi": "3.0.0",
        "info": {
            "title": "DTO 测试 API",
            "version": "1.0.0"
        },
        "paths": {},
        "components": {
            "schemas": {
                "Product": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    },
                    "required": ["id", "name"]
                }
            }
        }
    }
    
    payload = {"content": json.dumps(openapi_content)}
    result = requests.post(
        f"{BASE_URL}/v1/openapi/generate-dtos",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if result.status_code == 200:
        data = result.json()
        if data.get('success'):
            print("✅ DTO 生成成功!")
            print("完整的 DTO 结构:")
            print(json.dumps(data['data'], indent=2, ensure_ascii=False))
            
            # 分析第一个 DTO 的字段结构
            if data['data']:
                first_dto = data['data'][0]
                print(f"\n第一个 DTO: {first_dto['name']}")
                print("字段结构:")
                for field in first_dto['fields']:
                    print(f"  {field}")
        else:
            print(f"❌ DTO 生成失败: {data.get('error')}")
    else:
        print(f"❌ HTTP 请求失败: {result.text}")

if __name__ == "__main__":
    debug_dto_structure() 