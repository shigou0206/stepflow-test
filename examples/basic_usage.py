"""
StepFlow Gateway 基本使用示例
"""

import json
from stepflow_gateway import StepFlowGateway


def main():
    """基本使用示例"""
    print("=== StepFlow Gateway 基本使用示例 ===\n")
    
    # 1. 创建 Gateway 实例
    print("1. 创建 Gateway 实例...")
    gateway = StepFlowGateway()
    
    # 2. 初始化 Gateway
    print("2. 初始化 Gateway...")
    if not gateway.initialize():
        print("❌ 初始化失败")
        return
    
    print("✅ 初始化成功\n")
    
    # 3. 注册 OpenAPI 文档
    print("3. 注册 OpenAPI 文档...")
    
    # 示例 OpenAPI 文档
    petstore_openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": "Pet Store API",
            "version": "1.0.0",
            "description": "A sample Pet Store API"
        },
        "paths": {
            "/pets": {
                "get": {
                    "summary": "List all pets",
                    "operationId": "listPets",
                    "tags": ["pets"],
                    "responses": {
                        "200": {
                            "description": "A list of pets",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/Pet"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create a pet",
                    "operationId": "createPet",
                    "tags": ["pets"],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Pet"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Pet created successfully"
                        }
                    }
                }
            },
            "/pets/{petId}": {
                "get": {
                    "summary": "Get a pet by ID",
                    "operationId": "getPet",
                    "tags": ["pets"],
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "integer"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Pet found"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer"
                        },
                        "name": {
                            "type": "string"
                        },
                        "species": {
                            "type": "string"
                        }
                    }
                }
            }
        }
    }
    
    # 注册 API
    result = gateway.register_api(
        name="Pet Store API",
        openapi_content=json.dumps(petstore_openapi),
        version="1.0.0",
        base_url="https://api.petstore.com"
    )
    
    if not result['success']:
        print(f"❌ API 注册失败: {result['error']}")
        return
    
    api_document_id = result['document_id']
    print(f"✅ API 注册成功 (ID: {api_document_id})")
    print(f"   端点数量: {len(result['endpoints'])}")
    
    for endpoint in result['endpoints']:
        print(f"   - {endpoint['method']} {endpoint['path']}")
    
    print()
    
    # 4. 添加认证配置
    print("4. 添加认证配置...")
    
    # Basic 认证配置
    basic_auth_config = {
        "username": "admin",
        "password": "admin123"
    }
    
    auth_config_id = gateway.add_auth_config(
        api_document_id=api_document_id,
        auth_type="basic",
        auth_config=basic_auth_config,
        is_required=True,
        priority=10
    )
    
    print(f"✅ 添加 Basic 认证配置 (ID: {auth_config_id})")
    
    # API Key 认证配置
    api_key_config = {
        "key_name": "X-API-Key",
        "key_value": "your-api-key-here"
    }
    
    api_key_auth_id = gateway.add_auth_config(
        api_document_id=api_document_id,
        auth_type="api_key",
        auth_config=api_key_config,
        is_required=False,
        priority=5
    )
    
    print(f"✅ 添加 API Key 认证配置 (ID: {api_key_auth_id})")
    print()
    
    # 5. 列出 API 和端点
    print("5. 列出 API 和端点...")
    
    apis = gateway.list_apis()
    print(f"找到 {len(apis)} 个 API:")
    for api in apis:
        print(f"  - {api['name']} (ID: {api['id']})")
        print(f"    版本: {api.get('version', 'N/A')}")
        print(f"    基础URL: {api.get('base_url', 'N/A')}")
    
    print()
    
    endpoints = gateway.list_endpoints(api_document_id)
    print(f"找到 {len(endpoints)} 个端点:")
    for endpoint in endpoints:
        print(f"  - {endpoint['method']} {endpoint['path']} (ID: {endpoint['id']})")
        if endpoint.get('summary'):
            print(f"    描述: {endpoint['summary']}")
    
    print()
    
    # 6. 调用 API
    print("6. 调用 API...")
    
    # 获取第一个端点
    if endpoints:
        endpoint = endpoints[0]
        endpoint_id = endpoint['id']
        
        print(f"调用端点: {endpoint['method']} {endpoint['path']}")
        
        # 构建请求数据
        request_data = {
            'headers': {
                'Authorization': 'Basic YWRtaW46YWRtaW4xMjM=',  # admin:admin123
                'Content-Type': 'application/json'
            },
            'params': {
                'limit': 10
            },
            'client_ip': '192.168.1.100',
            'user_agent': 'StepFlow-Gateway-Example/1.0.0'
        }
        
        # 调用 API
        result = gateway.call_api(endpoint_id, request_data)
        
        if result['success']:
            print("✅ API 调用成功")
            print(f"   状态码: {result.get('status_code', 'N/A')}")
            print(f"   响应时间: {result.get('response_time_ms', 'N/A')}ms")
            print("   响应体:")
            print(json.dumps(result.get('body', {}), indent=4, ensure_ascii=False))
        else:
            print(f"❌ API 调用失败: {result['error']}")
    
    print()
    
    # 7. 查看统计信息
    print("7. 查看统计信息...")
    
    stats = gateway.get_statistics()
    print("系统统计:")
    print(f"  模板数量: {stats['templates']}")
    print(f"  API文档数量: {stats['api_documents']}")
    print(f"  端点数量: {stats['endpoints']}")
    print(f"  用户数量: {stats['users']}")
    print(f"  认证配置数量: {stats['auth_configs']}")
    print(f"  API调用总数: {stats['api_calls']}")
    
    print()
    
    # 8. 健康检查
    print("8. 健康检查...")
    
    health_result = gateway.check_health(api_document_id)
    if health_result['status'] == 'success':
        print("✅ API 健康状态良好")
    elif health_result['status'] == 'warning':
        print("⚠️  API 健康状态警告")
    else:
        print("❌ API 健康状态异常")
    
    print(f"  总端点数: {health_result.get('total_endpoints', 0)}")
    print(f"  活跃端点数: {health_result.get('active_endpoints', 0)}")
    
    print()
    
    # 9. 用户管理
    print("9. 用户管理...")
    
    # 列出用户
    users = gateway.list_users()
    print(f"找到 {len(users)} 个用户:")
    for user in users:
        print(f"  - {user['username']} (角色: {user['role']})")
    
    # 创建新用户
    try:
        new_user_id = gateway.create_user(
            username="test_user",
            email="test@example.com",
            password="test123",
            role="user"
        )
        print(f"✅ 创建用户成功 (ID: {new_user_id})")
    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
    
    print()
    
    # 10. 认证配置管理
    print("10. 认证配置管理...")
    
    auth_configs = gateway.list_auth_configs(api_document_id)
    print(f"找到 {len(auth_configs)} 个认证配置:")
    for config in auth_configs:
        print(f"  - {config['auth_type']} (优先级: {config['priority']})")
        print(f"    必需: {config['is_required']}")
        print(f"    全局: {config['is_global']}")
    
    print()
    
    # 11. 资源引用管理
    print("11. 资源引用管理...")
    
    if endpoints:
        endpoint = endpoints[0]
        
        # 创建资源引用
        ref_id = gateway.create_resource_reference(
            resource_type="workflow_node",
            resource_id="node_123",
            api_endpoint_id=endpoint['id'],
            display_name="获取宠物列表",
            description="用于工作流中获取宠物列表的API调用"
        )
        
        print(f"✅ 创建资源引用成功 (ID: {ref_id})")
        
        # 获取资源引用
        refs = gateway.get_resource_references("workflow_node")
        print(f"找到 {len(refs)} 个工作流节点引用:")
        for ref in refs:
            print(f"  - {ref['display_name']} -> {ref['resource_id']}")
    
    print()
    
    # 12. 关闭 Gateway
    print("12. 关闭 Gateway...")
    gateway.close()
    print("✅ Gateway 已关闭")
    
    print("\n=== 示例完成 ===")


if __name__ == '__main__':
    main() 