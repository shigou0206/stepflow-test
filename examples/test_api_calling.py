#!/usr/bin/env python3
"""
测试 API 调用功能
演示如何注册 OpenAPI 文档并直接调用其中的 API
"""

import json
import sys
import os
import requests
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 一个真实的 API 文档示例（JSONPlaceholder API）
JSONPLACEHOLDER_OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "JSONPlaceholder API",
        "version": "1.0.0",
        "description": "Fake Online REST API for Testing and Prototyping"
    },
    "servers": [
        {
            "url": "https://jsonplaceholder.typicode.com",
            "description": "JSONPlaceholder API server"
        }
    ],
    "paths": {
        "/posts": {
            "get": {
                "summary": "Get all posts",
                "operationId": "getPosts",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "title": {"type": "string"},
                                            "body": {"type": "string"},
                                            "userId": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Create a new post",
                "operationId": "createPost",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "body": {"type": "string"},
                                    "userId": {"type": "integer"}
                                },
                                "required": ["title", "body", "userId"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Post created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "title": {"type": "string"},
                                        "body": {"type": "string"},
                                        "userId": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/posts/{postId}": {
            "get": {
                "summary": "Get post by ID",
                "operationId": "getPostById",
                "parameters": [
                    {
                        "name": "postId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                        "description": "Post ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "title": {"type": "string"},
                                        "body": {"type": "string"},
                                        "userId": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Post not found"
                    }
                }
            }
        },
        "/users": {
            "get": {
                "summary": "Get all users",
                "operationId": "getUsers",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string"},
                                            "username": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

def test_api_registration_and_calling():
    """测试 API 注册和调用"""
    base_url = "http://localhost:8000"
    
    print("🚀 测试 API 注册和调用功能")
    print("=" * 50)
    
    # 1. 注册 API 文档
    print("\n1. 注册 JSONPlaceholder API 文档...")
    register_data = {
        "name": "JSONPlaceholder API",
        "openapi_content": json.dumps(JSONPLACEHOLDER_OPENAPI),
        "version": "1.0.0",
        "base_url": "https://jsonplaceholder.typicode.com"
    }
    
    response = requests.post(f"{base_url}/apis/register", json=register_data)
    print(f"   状态: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ 注册失败: {response.text}")
        return
    
    api_result = response.json()
    print(f"   ✅ 注册成功: {api_result}")
    
    document_id = api_result.get("document_id")
    endpoints = api_result.get("endpoints", [])
    
    if not document_id or not endpoints:
        print("   ❌ 注册结果无效")
        return
    
    # 2. 查看注册的端点
    print(f"\n2. 查看注册的端点 ({len(endpoints)} 个)...")
    for endpoint in endpoints:
        print(f"   - {endpoint['method']} {endpoint['path']}: {endpoint['summary']}")
    
    # 3. 调用 API - 获取所有文章
    print("\n3. 调用 API - 获取所有文章...")
    get_posts_endpoint = next((e for e in endpoints if e['path'] == '/posts' and e['method'] == 'GET'), None)
    
    if get_posts_endpoint:
        api_call_data = {
            "endpoint_id": get_posts_endpoint['id'],
            "request_data": {
                "method": "GET",
                "url": "https://jsonplaceholder.typicode.com/posts",
                "headers": {
                    "Content-Type": "application/json"
                },
                "params": {},
                "body": None
            }
        }
        
        response = requests.post(f"{base_url}/api/call", json=api_call_data)
        print(f"   状态: {response.status_code}")
        call_result = response.json()
        
        if call_result.get('success'):
            print("   ✅ 调用成功")
            posts = call_result.get('response_body', [])
            if isinstance(posts, list):
                print(f"   获取到 {len(posts)} 篇文章")
                if posts:
                    print(f"   第一篇文章标题: {posts[0].get('title', 'N/A')}")
        else:
            print(f"   ❌ 调用失败: {call_result.get('error')}")
    
    # 4. 调用 API - 获取特定文章
    print("\n4. 调用 API - 获取特定文章 (ID: 1)...")
    get_post_endpoint = next((e for e in endpoints if e['path'] == '/posts/{postId}' and e['method'] == 'GET'), None)
    
    if get_post_endpoint:
        api_call_data = {
            "endpoint_id": get_post_endpoint['id'],
            "request_data": {
                "method": "GET",
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "headers": {
                    "Content-Type": "application/json"
                },
                "params": {},
                "body": None
            }
        }
        
        response = requests.post(f"{base_url}/api/call", json=api_call_data)
        print(f"   状态: {response.status_code}")
        call_result = response.json()
        
        if call_result.get('success'):
            print("   ✅ 调用成功")
            post = call_result.get('response_body', {})
            if isinstance(post, dict):
                print(f"   文章标题: {post.get('title', 'N/A')}")
                print(f"   作者 ID: {post.get('userId', 'N/A')}")
        else:
            print(f"   ❌ 调用失败: {call_result.get('error')}")
    
    # 5. 调用 API - 创建新文章
    print("\n5. 调用 API - 创建新文章...")
    create_post_endpoint = next((e for e in endpoints if e['path'] == '/posts' and e['method'] == 'POST'), None)
    
    if create_post_endpoint:
        new_post_data = {
            "title": "Test Post via StepFlow Gateway",
            "body": "This post was created through the StepFlow Gateway API",
            "userId": 1
        }
        
        api_call_data = {
            "endpoint_id": create_post_endpoint['id'],
            "request_data": {
                "method": "POST",
                "url": "https://jsonplaceholder.typicode.com/posts",
                "headers": {
                    "Content-Type": "application/json"
                },
                "params": {},
                "body": json.dumps(new_post_data)
            }
        }
        
        response = requests.post(f"{base_url}/api/call", json=api_call_data)
        print(f"   状态: {response.status_code}")
        call_result = response.json()
        
        if call_result.get('success'):
            print("   ✅ 调用成功")
            created_post = call_result.get('response_body', {})
            if isinstance(created_post, dict):
                print(f"   创建的文章 ID: {created_post.get('id', 'N/A')}")
                print(f"   文章标题: {created_post.get('title', 'N/A')}")
        else:
            print(f"   ❌ 调用失败: {call_result.get('error')}")
    
    # 6. 通过路径调用 API
    print("\n6. 通过路径调用 API - 获取所有用户...")
    path_call_data = {
        "method": "GET",
        "url": "https://jsonplaceholder.typicode.com/users",
        "headers": {
            "Content-Type": "application/json"
        },
        "params": {},
        "body": None
    }
    
    response = requests.post(
        f"{base_url}/api/call/path?path=/users&method=GET&api_document_id={document_id}",
        json=path_call_data
    )
    print(f"   状态: {response.status_code}")
    path_call_result = response.json()
    
    if path_call_result.get('success'):
        print("   ✅ 路径调用成功")
        users = path_call_result.get('response_body', [])
        if isinstance(users, list):
            print(f"   获取到 {len(users)} 个用户")
            if users:
                print(f"   第一个用户: {users[0].get('name', 'N/A')}")
    else:
        print(f"   ❌ 路径调用失败: {path_call_result.get('error')}")
    
    # 7. 查看调用统计
    print("\n7. 查看调用统计...")
    response = requests.get(f"{base_url}/statistics")
    if response.status_code == 200:
        stats = response.json()
        print(f"   API 调用次数: {stats.get('api_calls', 0)}")
    
    # 8. 查看最近的调用日志
    print("\n8. 查看最近的调用日志...")
    response = requests.get(f"{base_url}/logs/recent", params={"limit": 5})
    if response.status_code == 200:
        logs = response.json()
        recent_calls = logs.get('recent_calls', [])
        print(f"   最近 {len(recent_calls)} 次调用:")
        for call in recent_calls:
            print(f"   - {call.get('method', 'N/A')} {call.get('path', 'N/A')}: {call.get('response_status_code', 'N/A')}")
    
    print("\n🎉 API 注册和调用测试完成！")

def test_with_real_api():
    """测试真实的 API 调用"""
    print("\n🔗 测试真实 API 调用")
    print("=" * 30)
    
    # 直接调用 JSONPlaceholder API 进行对比
    print("直接调用 JSONPlaceholder API...")
    response = requests.get("https://jsonplaceholder.typicode.com/posts/1")
    if response.status_code == 200:
        post = response.json()
        print(f"   直接调用结果: {post.get('title', 'N/A')}")
    
    print("通过 StepFlow Gateway 调用...")
    # 这里可以添加通过网关的调用对比

if __name__ == "__main__":
    test_api_registration_and_calling()
    test_with_real_api()