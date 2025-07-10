#!/usr/bin/env python3
"""
测试 StepFlow Gateway 的各种认证机制
"""
import json
import requests
import time

BASE_URL = "http://localhost:8000"

# 示例 OpenAPI 文档，包含一个 /auth-test 端点
OPENAPI_DOC = {
    "openapi": "3.0.0",
    "info": {"title": "Auth Test API", "version": "1.0.0"},
    "servers": [{"url": "https://httpbin.org", "description": "httpbin server"}],
    "paths": {
        "/basic-auth/user/pass": {
            "get": {
                "summary": "Basic Auth Test",
                "operationId": "basicAuthTest",
                "responses": {"200": {"description": "OK"}}
            }
        },
        "/bearer": {
            "get": {
                "summary": "Bearer Auth Test",
                "operationId": "bearerAuthTest",
                "responses": {"200": {"description": "OK"}}
            }
        },
        "/api-key-header": {
            "get": {
                "summary": "API Key Header Test",
                "operationId": "apiKeyHeaderTest",
                "parameters": [
                    {"name": "X-API-KEY", "in": "header", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        },
        "/api-key-query": {
            "get": {
                "summary": "API Key Query Test",
                "operationId": "apiKeyQueryTest",
                "parameters": [
                    {"name": "api_key", "in": "query", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        },
        "/oauth2/token": {
            "get": {
                "summary": "OAuth2 Token Test (模拟)",
                "operationId": "oauth2TokenTest",
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
}

def register_api():
    print("\n1. 注册 Auth Test API 文档...")
    data = {
        "name": "Auth Test API",
        "openapi_content": json.dumps(OPENAPI_DOC),
        "version": "1.0.0",
        "base_url": "https://httpbin.org"
    }
    resp = requests.post(f"{BASE_URL}/apis/register", json=data)
    result = resp.json()
    print("   注册结果:", result)
    return result.get("document_id"), result.get("endpoints", [])

def add_auth_config(api_document_id, auth_type, auth_config, summary):
    print(f"\n2. 配置认证: {summary} ({auth_type}) ...")
    data = {
        "api_document_id": api_document_id,
        "auth_type": auth_type,
        "auth_config": auth_config,
        "is_required": True,
        "is_global": False,
        "priority": 1
    }
    resp = requests.post(f"{BASE_URL}/auth/configs", json=data)
    print("   配置结果:", resp.json())

def call_endpoint(endpoint, request_data, summary):
    print(f"\n3. 调用 {summary} ...")
    data = {
        "endpoint_id": endpoint["id"],
        "request_data": request_data
    }
    resp = requests.post(f"{BASE_URL}/api/call", json=data)
    try:
        result = resp.json()
    except Exception:
        result = resp.text
    print("   响应:", result)
    return result

def main():
    # 注册 API
    api_document_id, endpoints = register_api()
    if not api_document_id:
        print("注册失败，退出测试。")
        return

    # 获取各端点
    ep_basic = next(e for e in endpoints if e["path"] == "/basic-auth/user/pass")
    ep_bearer = next(e for e in endpoints if e["path"] == "/bearer")
    ep_key_header = next(e for e in endpoints if e["path"] == "/api-key-header")
    ep_key_query = next(e for e in endpoints if e["path"] == "/api-key-query")
    # ep_oauth2 = next(e for e in endpoints if e["path"] == "/oauth2/token")

    # 1. Basic Auth
    add_auth_config(api_document_id, "basic", {"username": "user", "password": "pass"}, "Basic Auth")
    call_endpoint(ep_basic, {"method": "GET", "url": "https://httpbin.org/basic-auth/user/pass"}, "Basic Auth 认证端点")

    # 2. Bearer Token
    add_auth_config(api_document_id, "bearer", {"token": "test-bearer-token"}, "Bearer Token")
    call_endpoint(ep_bearer, {"method": "GET", "url": "https://httpbin.org/bearer"}, "Bearer Token 认证端点")

    # 3. API Key (Header)
    add_auth_config(api_document_id, "api_key", {"in": "header", "name": "X-API-KEY", "value": "test-key-header"}, "API Key Header")
    call_endpoint(ep_key_header, {"method": "GET", "url": "https://httpbin.org/api-key-header"}, "API Key Header 认证端点")

    # 4. API Key (Query)
    add_auth_config(api_document_id, "api_key", {"in": "query", "name": "api_key", "value": "test-key-query"}, "API Key Query")
    call_endpoint(ep_key_query, {"method": "GET", "url": "https://httpbin.org/api-key-query"}, "API Key Query 认证端点")

    # 5. OAuth2（如需真实测试可补充完整流程）
    # add_auth_config(api_document_id, "oauth2", {"access_token": "test-oauth2-token"}, "OAuth2 Token")
    # call_endpoint(ep_oauth2, {"method": "GET", "url": "https://httpbin.org/oauth2/token"}, "OAuth2 认证端点")

if __name__ == "__main__":
    main() 