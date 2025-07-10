#!/usr/bin/env python3
import requests
import yaml
import json

BASE_URL = 'http://localhost:3000'

def assert_true(expr, msg):
    if expr:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")

def test_petstore_json():
    print("🔍 测试 pet_store.json ...")
    with open("templates/pet_store.json", "r", encoding="utf-8") as f:
        json_raw = f.read()
    payload = {
        "content": json_raw
    }
    endpoints = [
        ("/v1/openapi/parse", "解析 OpenAPI 文档"),
        ("/v1/openapi/validate", "验证 OpenAPI 文档"),
        ("/v1/openapi/generate-dtos", "生成 DTO 结构"),
    ]
    results = {}
    for endpoint, desc in endpoints:
        print(f"\n--- {desc} ({endpoint}) ---")
        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            results[endpoint] = response.json()
        except Exception as e:
            print(f"错误: {e}")

    # 解析接口断言
    parse_data = results.get("/v1/openapi/parse", {})
    if parse_data.get("success"):
        info = parse_data["data"]["info"]
        assert_true(info["title"] == "Swagger Petstore - OpenAPI 3.0", "info.title 正确")
        assert_true(info["version"] == "1.0.12", "info.version 正确")
        assert_true("servers" in parse_data["data"]["info"], "info.servers 存在")
        assert_true(len(parse_data["data"]["paths"]) > 0, "paths 非空")
        # 检查所有 paths 都被解析
        with open("templates/pet_store.json", "r", encoding="utf-8") as f:
            petstore_obj = json.load(f)
        all_paths = set(petstore_obj.get("paths", {}).keys())
        parsed_paths = set(p["path"] for p in parse_data["data"]["paths"])
        assert_true(all_paths.issubset(parsed_paths), "所有 paths 都被解析")
    else:
        print("❌ 解析接口未通过")

    # 验证接口断言
    validate_data = results.get("/v1/openapi/validate", {})
    if validate_data.get("success"):
        assert_true(validate_data["data"]["is_valid"], "文档验证通过")
        assert_true(len(validate_data["data"]["errors"]) == 0, "无 errors")
        assert_true(len(validate_data["data"]["warnings"]) == 0, "无 warnings")
    else:
        print("❌ 验证接口未通过")

    # DTO 结构断言
    dtos_data = results.get("/v1/openapi/generate-dtos", {})
    if dtos_data.get("success"):
        dtos = dtos_data["data"]
        dto_names = [dto["name"] for dto in dtos]
        assert_true("User" in dto_names, "User DTO 存在")
        assert_true("Pet" in dto_names, "Pet DTO 存在")
        # 检查所有 schema 都能生成 DTO
        with open("templates/pet_store.json", "r", encoding="utf-8") as f:
            petstore_obj = json.load(f)
        all_schemas = set(petstore_obj.get("components", {}).get("schemas", {}).keys())
        assert_true(all_schemas.issubset(set(dto_names)), "所有 schema 都能生成 DTO")
        # 检查 DTO 字段类型和 is_required
        for dto in dtos:
            for field in dto["fields"]:
                assert_true("field_type" in field, f"{dto['name']}.{field['name']} 有 field_type")
                assert_true("is_required" in field, f"{dto['name']}.{field['name']} 有 is_required")
        # 检查 DTO 名称和字段名唯一性
        assert_true(len(dto_names) == len(set(dto_names)), "所有 DTO 名称唯一")
        for dto in dtos:
            field_names = [f["name"] for f in dto["fields"]]
            assert_true(len(field_names) == len(set(field_names)), f"{dto['name']} 字段名唯一")
    else:
        print("❌ DTO 生成接口未通过")

    # 错误场景：缺 info 字段
    print("\n--- 错误场景测试：缺 info 字段 ---")
    with open("templates/pet_store.json", "r", encoding="utf-8") as f:
        petstore_obj = json.load(f)
    petstore_obj_missing_info = dict(petstore_obj)
    petstore_obj_missing_info.pop("info", None)
    payload_err = {"content": json.dumps(petstore_obj_missing_info)}
    response_err = requests.post(f"{BASE_URL}/v1/openapi/parse", json=payload_err, headers={"Content-Type": "application/json"})
    err_data = response_err.json()
    assert_true(not err_data.get("success"), "缺 info 字段时解析失败")
    print(f"错误信息: {err_data.get('error')}")

if __name__ == "__main__":
    # 自动生成 json
    with open("templates/pet_store.yml", "r", encoding="utf-8") as f:
        yml_content = yaml.safe_load(f)
    with open("templates/pet_store.json", "w", encoding="utf-8") as f:
        json.dump(yml_content, f, ensure_ascii=False, indent=2)
    test_petstore_json()