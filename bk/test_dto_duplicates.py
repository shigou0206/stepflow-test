#!/usr/bin/env python3
import requests
import json

BASE_URL = 'http://localhost:3000'

def assert_true(expr, msg):
    if expr:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")

def test_dto_name_duplicates():
    """测试DTO名称重复问题"""
    print("🔍 测试DTO名称重复问题...")
    
    # 创建一个包含重复DTO名称的OpenAPI文档
    openapi_content = {
        "openapi": "3.0.0",
        "info": {
            "title": "DTO 重复测试 API",
            "version": "1.0.0"
        },
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    },
                    "required": ["id", "name"]
                },
                "User": {  # 重复的DTO名称
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "email": {"type": "string"}
                    },
                    "required": ["id", "email"]
                },
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
            dtos = data['data']
            dto_names = [dto["name"] for dto in dtos]
            
            print(f"生成的DTO数量: {len(dtos)}")
            print(f"DTO名称列表: {dto_names}")
            
            # 检查是否有重复的DTO名称
            unique_names = set(dto_names)
            has_duplicates = len(dto_names) != len(unique_names)
            
            if has_duplicates:
                print("❌ 发现重复的DTO名称!")
                # 找出重复的名称
                duplicates = [name for name in unique_names if dto_names.count(name) > 1]
                print(f"重复的DTO名称: {duplicates}")
                
                # 显示重复的DTO详情
                for dup_name in duplicates:
                    dup_dtos = [dto for dto in dtos if dto["name"] == dup_name]
                    print(f"\n重复的DTO '{dup_name}' 详情:")
                    for i, dto in enumerate(dup_dtos):
                        print(f"  版本 {i+1}:")
                        for field in dto["fields"]:
                            print(f"    - {field['name']}: {field['field_type']}")
            else:
                print("✅ 所有DTO名称都是唯一的")
                
            # 断言检查
            assert_true(not has_duplicates, "所有DTO名称应该唯一")
            
        else:
            print(f"❌ DTO生成失败: {data.get('error')}")
            assert_true(False, "DTO生成应该成功")
    else:
        print(f"❌ HTTP请求失败: {result.text}")
        assert_true(False, "HTTP请求应该成功")

def test_dto_field_name_duplicates():
    """测试DTO字段名称重复问题"""
    print("\n🔍 测试DTO字段名称重复问题...")
    
    openapi_content = {
        "openapi": "3.0.0",
        "info": {
            "title": "DTO字段重复测试 API",
            "version": "1.0.0"
        },
        "paths": {},
        "components": {
            "schemas": {
                "Product": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "name": {"type": "string"}  # 重复的字段名
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
            dtos = data['data']
            
            for dto in dtos:
                field_names = [field["name"] for field in dto["fields"]]
                unique_field_names = set(field_names)
                has_duplicate_fields = len(field_names) != len(unique_field_names)
                
                print(f"DTO '{dto['name']}' 字段名称: {field_names}")
                
                if has_duplicate_fields:
                    print(f"❌ DTO '{dto['name']}' 有重复字段名!")
                    duplicates = [name for name in unique_field_names if field_names.count(name) > 1]
                    print(f"重复的字段名: {duplicates}")
                else:
                    print(f"✅ DTO '{dto['name']}' 字段名唯一")
                
                # 断言检查
                assert_true(not has_duplicate_fields, f"DTO '{dto['name']}' 字段名应该唯一")
        else:
            print(f"❌ DTO生成失败: {data.get('error')}")
            assert_true(False, "DTO生成应该成功")
    else:
        print(f"❌ HTTP请求失败: {result.text}")
        assert_true(False, "HTTP请求应该成功")

def main():
    """主函数"""
    print("🚀 DTO重复名称测试")
    print("=" * 50)
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/v1/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print("❌ 服务器响应异常")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到服务器，请确保 StepFlow Gateway 正在运行")
        return
    
    # 运行测试
    test_dto_name_duplicates()
    test_dto_field_name_duplicates()
    
    print("\n" + "=" * 50)
    print("🎉 DTO重复名称测试完成!")

if __name__ == "__main__":
    main() 