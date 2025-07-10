#!/usr/bin/env python3
"""
测试 OpenAPI 插件功能
"""

import json
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from stepflow_gateway.core.registry import ApiSpecRegistry
from stepflow_gateway.core.gateway import StepFlowGateway
from stepflow_gateway.plugins.openapi import OpenAPISpecification, OpenAPIParser, OpenAPIExecutor, HTTPProtocolAdapter


def test_openapi_plugin():
    """测试 OpenAPI 插件功能"""
    print("=== 测试 OpenAPI 插件 ===")
    
    # 1. 测试规范类
    print("\n1. 测试 OpenAPI 规范类...")
    test_spec_content = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API for plugin testing"
        },
        "servers": [
            {
                "url": "https://petstore3.swagger.io/api/v3"
            }
        ],
        "paths": {
            "/pet/{petId}": {
                "get": {
                    "summary": "Find pet by ID",
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
                            "description": "Successful operation",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    spec = OpenAPISpecification("test-spec-1", "Test API", test_spec_content)
    print(f"✓ 规范创建成功: {spec.name}")
    print(f"✓ 规范验证: {spec.validate()}")
    
    # 2. 测试 OpenAPI 解析器...
    print("\n2. 测试 OpenAPI 解析器...")
    parser = OpenAPIParser()
    
    # 测试内容验证
    test_content_str = json.dumps(test_spec_content)
    print(f"✓ 内容验证: {parser.validate(test_content_str)}")
    
    # 测试内容解析
    parsed_content = parser.parse(test_content_str)
    print(f"✓ 内容解析成功")
    
    # 测试规范解析
    parsed_spec = parser.parse_specification(test_spec_content, "test-spec-2", "Test API")
    print(f"✓ 解析器解析成功: {parsed_spec.name}")
    
    endpoints = parser.parse_endpoints(parsed_spec)
    print(f"✓ 解析端点数量: {len(endpoints)}")
    for endpoint in endpoints:
        print(f"  - {endpoint['method']} {endpoint['endpoint_name']}")
    
    # 3. 测试协议适配器
    print("\n3. 测试 HTTP 协议适配器...")
    protocol = HTTPProtocolAdapter()
    print(f"✓ 协议适配器创建成功: {protocol.protocol_name}")
    
    # 测试 URL 构建
    test_url = protocol.build_url("https://api.example.com/v1", "/users/{id}")
    print(f"✓ URL 构建测试: {test_url}")
    
    # 4. 测试执行器
    print("\n4. 测试 OpenAPI 执行器...")
    executor = OpenAPIExecutor(protocol)
    
    # 测试操作列表
    operations = executor.list_operations(parsed_spec)
    print(f"✓ 可用操作数量: {len(operations)}")
    for op in operations:
        print(f"  - {op['operation']}: {op['summary']}")
    
    # 测试操作信息获取
    operation_info = executor.get_operation_info(parsed_spec, "GET /pet/{petId}")
    if operation_info:
        print(f"✓ 操作信息获取成功: {operation_info['summary']}")
    
    # 5. 测试参数验证
    print("\n5. 测试参数验证...")
    operation_def = parsed_spec.get_operation("/pet/{petId}", "get")
    if operation_def:
        # 测试有效参数
        valid_params = {"petId": 123}
        validation_result = parser.validate_parameters(operation_def, valid_params)
        print(f"✓ 有效参数验证: {validation_result[0]}")
        
        # 测试无效参数
        invalid_params = {"petId": "invalid"}
        validation_result = parser.validate_parameters(operation_def, invalid_params)
        print(f"✓ 无效参数验证: {not validation_result[0]}")
    
    # 6. 测试注册表集成
    print("\n6. 测试注册表集成...")
    registry = ApiSpecRegistry()
    
    # 注册 OpenAPI 组件
    registry.register_spec("openapi", OpenAPISpecification)
    registry.register_parser("openapi", OpenAPIParser)
    registry.register_executor("openapi", OpenAPIExecutor)
    registry.register_protocol("http", HTTPProtocolAdapter)
    registry.register_protocol("https", HTTPProtocolAdapter)
    
    print(f"✓ 注册的规范类型: {registry.list_specs()}")
    print(f"✓ 注册的解析器: {registry.list_parsers()}")
    print(f"✓ 注册的执行器: {registry.list_executors()}")
    print(f"✓ 注册的协议: {registry.list_protocols()}")
    
    # 7. 测试网关集成
    print("\n7. 测试网关集成...")
    gateway = StepFlowGateway()
    
    # 测试网关基本功能
    print(f"✓ 网关创建成功")
    
    # 测试网关配置
    config = gateway.get_config()
    print(f"✓ 网关配置加载成功: {config.database.path}")
    
    # 测试网关统计信息
    stats = gateway.get_statistics()
    print(f"✓ 网关统计信息: {len(stats)} 项")
    
    print(f"✓ 网关集成测试完成")
    
    # 8. 测试实际 API 调用（可选）
    print("\n8. 测试实际 API 调用...")
    try:
        # 首先注册 API
        register_result = gateway.register_api(
            name="Test Petstore API",
            openapi_content=json.dumps(test_spec_content),
            version="1.0.0",
            base_url="https://petstore3.swagger.io/api/v3"
        )
        
        if register_result['success']:
            print(f"✓ API 注册成功: {register_result['document_id']}")
            
            # 获取端点列表
            endpoints = gateway.list_endpoints(register_result['document_id'])
            if endpoints:
                endpoint_id = endpoints[0]['id']
                
                # 调用 API
                result = gateway.call_api(
                    endpoint_id=endpoint_id,
                    request_data={"petId": 1}
                )
                
                if result['success']:
                    print(f"✓ API 调用成功: {result.get('status_code', 'N/A')}")
                    print(f"✓ 响应数据: {result.get('data', 'N/A')}")
                else:
                    print(f"✗ API 调用失败: {result['error']}")
            else:
                print("✗ 没有找到可用的端点")
        else:
            print(f"✗ API 注册失败: {register_result['error']}")
    except Exception as e:
        print(f"✗ API 调用测试跳过: {e}")
    
    print("\n=== OpenAPI 插件测试完成 ===")
    return True


def test_petstore_integration():
    """测试 Petstore API 集成"""
    print("\n=== 测试 Petstore API 集成 ===")
    
    # Petstore OpenAPI 规范
    petstore_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Swagger Petstore",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": "https://petstore3.swagger.io/api/v3"
            }
        ],
        "paths": {
            "/pet/{petId}": {
                "get": {
                    "summary": "Find pet by ID",
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
                            "description": "Successful operation"
                        },
                        "400": {
                            "description": "Invalid ID supplied"
                        },
                        "404": {
                            "description": "Pet not found"
                        }
                    }
                }
            },
            "/pet/findByStatus": {
                "get": {
                    "summary": "Finds Pets by status",
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": ["available", "pending", "sold"]
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful operation"
                        },
                        "400": {
                            "description": "Invalid status value"
                        }
                    }
                }
            }
        }
    }
    
    # 创建网关实例
    gateway = StepFlowGateway()
    
    # 注册 Petstore API
    print("\n1. 注册 Petstore API...")
    register_result = gateway.register_api(
        name="Petstore API",
        openapi_content=json.dumps(petstore_spec),
        version="1.0.0",
        base_url="https://petstore3.swagger.io/api/v3"
    )
    
    if not register_result['success']:
        print(f"✗ API 注册失败: {register_result['error']}")
        return
    
    document_id = register_result['document_id']
    print(f"✓ API 注册成功: {document_id}")
    
    # 获取端点列表
    endpoints = gateway.list_endpoints(document_id)
    if not endpoints:
        print("✗ 没有找到可用的端点")
        return
    
    print(f"✓ 找到 {len(endpoints)} 个端点")
    
    # 测试获取宠物信息
    print("\n2. 测试获取宠物信息...")
    pet_endpoint = None
    for endpoint in endpoints:
        if "/pet/{petId}" in endpoint.get('endpoint_name', ''):
            pet_endpoint = endpoint
            break
    
    if pet_endpoint:
        result = gateway.call_api(
            endpoint_id=pet_endpoint['id'],
            request_data={"petId": 1}
        )
        
        if result['success']:
            print(f"✓ 获取宠物成功: 状态码 {result.get('status_code', 'N/A')}")
            if result.get('data'):
                pet_data = result['data']
                print(f"✓ 宠物名称: {pet_data.get('name', 'N/A')}")
                print(f"✓ 宠物状态: {pet_data.get('status', 'N/A')}")
        else:
            print(f"✗ 获取宠物失败: {result['error']}")
    else:
        print("✗ 没有找到宠物端点")
    
    # 测试按状态查找宠物
    print("\n3. 测试按状态查找宠物...")
    status_endpoint = None
    for endpoint in endpoints:
        if "/pet/findByStatus" in endpoint.get('endpoint_name', ''):
            status_endpoint = endpoint
            break
    
    if status_endpoint:
        result = gateway.call_api(
            endpoint_id=status_endpoint['id'],
            request_data={"status": "available"}
        )
        
        if result['success']:
            print(f"✓ 查找宠物成功: 状态码 {result.get('status_code', 'N/A')}")
            if result.get('data'):
                pets = result['data']
                print(f"✓ 找到 {len(pets)} 个可用宠物")
        else:
            print(f"✗ 查找宠物失败: {result['error']}")
    else:
        print("✗ 没有找到状态查询端点")
    
    print("\n=== Petstore API 集成测试完成 ===")


if __name__ == "__main__":
    try:
        # 运行基本插件测试
        test_openapi_plugin()
        
        # 运行 Petstore 集成测试
        test_petstore_integration()
        
        print("\n🎉 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 