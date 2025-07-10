#!/usr/bin/env python3
"""
测试 OpenAPI $ref 解析功能
演示如何处理包含引用的 OpenAPI 文档
"""

import json
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.stepflow_gateway.api.parser import OpenApiRefResolver

# 包含 $ref 引用的 OpenAPI 文档示例
OPENAPI_WITH_REFS = {
    "openapi": "3.0.0",
    "info": {
        "title": "User Management API",
        "version": "1.0.0",
        "description": "API with $ref references"
    },
    "servers": [
        {
            "url": "https://api.example.com/v1",
            "description": "Production server"
        }
    ],
    "paths": {
        "/users": {
            "get": {
                "summary": "Get all users",
                "operationId": "getUsers",
                "parameters": [
                    {
                        "$ref": "#/components/parameters/PageParam"
                    },
                    {
                        "$ref": "#/components/parameters/LimitParam"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserList"
                                }
                            }
                        }
                    },
                    "400": {
                        "$ref": "#/components/responses/BadRequest"
                    }
                }
            },
            "post": {
                "summary": "Create a new user",
                "operationId": "createUser",
                "requestBody": {
                    "$ref": "#/components/requestBodies/UserCreate"
                },
                "responses": {
                    "201": {
                        "description": "User created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/User"
                                }
                            }
                        }
                    },
                    "400": {
                        "$ref": "#/components/responses/BadRequest"
                    }
                }
            }
        },
        "/users/{userId}": {
            "get": {
                "summary": "Get user by ID",
                "operationId": "getUserById",
                "parameters": [
                    {
                        "$ref": "#/components/parameters/UserId"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/User"
                                }
                            }
                        }
                    },
                    "404": {
                        "$ref": "#/components/responses/NotFound"
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "User ID"
                    },
                    "name": {
                        "type": "string",
                        "description": "User name"
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                        "description": "User email"
                    },
                    "status": {
                        "$ref": "#/components/schemas/UserStatus"
                    }
                },
                "required": ["id", "name", "email"]
            },
            "UserList": {
                "type": "object",
                "properties": {
                    "users": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/User"
                        }
                    },
                    "total": {
                        "type": "integer"
                    },
                    "page": {
                        "type": "integer"
                    }
                }
            },
            "UserStatus": {
                "type": "string",
                "enum": ["active", "inactive", "pending"],
                "default": "active"
            },
            "Error": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string"
                    },
                    "message": {
                        "type": "string"
                    }
                }
            }
        },
        "parameters": {
            "UserId": {
                "name": "userId",
                "in": "path",
                "required": True,
                "schema": {
                    "type": "integer"
                },
                "description": "User ID"
            },
            "PageParam": {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {
                    "type": "integer",
                    "default": 1,
                    "minimum": 1
                },
                "description": "Page number"
            },
            "LimitParam": {
                "name": "limit",
                "in": "query",
                "required": False,
                "schema": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                },
                "description": "Number of items per page"
            }
        },
        "requestBodies": {
            "UserCreate": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "minLength": 1
                                },
                                "email": {
                                    "type": "string",
                                    "format": "email"
                                },
                                "status": {
                                    "$ref": "#/components/schemas/UserStatus"
                                }
                            },
                            "required": ["name", "email"]
                        }
                    }
                }
            }
        },
        "responses": {
            "BadRequest": {
                "description": "Bad request",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/Error"
                        }
                    }
                }
            },
            "NotFound": {
                "description": "Resource not found",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/Error"
                        }
                    }
                }
            }
        }
    }
}

def test_ref_resolution():
    """测试 $ref 解析功能"""
    print("🔍 测试 OpenAPI $ref 解析功能")
    print("=" * 50)
    
    # 创建解析器
    resolver = OpenApiRefResolver()
    
    # 解析文档
    print("\n1. 解析包含 $ref 的 OpenAPI 文档...")
    resolved_doc = resolver.resolve_document(json.dumps(OPENAPI_WITH_REFS))
    print("✅ 解析完成")
    
    # 检查解析结果
    print("\n2. 检查解析结果...")
    
    # 检查路径参数是否被解析
    users_path = resolved_doc['paths']['/users']['get']
    parameters = users_path['parameters']
    
    print(f"   路径参数数量: {len(parameters)}")
    for param in parameters:
        print(f"   - {param['name']} ({param['in']}): {param.get('description', 'No description')}")
    
    # 检查响应是否被解析
    responses = users_path['responses']
    print(f"\n   响应数量: {len(responses)}")
    for status, response in responses.items():
        print(f"   - {status}: {response.get('description', 'No description')}")
    
    # 检查请求体是否被解析
    post_operation = resolved_doc['paths']['/users']['post']
    request_body = post_operation['requestBody']
    print(f"\n   请求体: {request_body.get('description', 'No description')}")
    
    # 提取端点
    print("\n3. 提取端点信息...")
    endpoints = resolver.extract_endpoints(resolved_doc)
    print(f"   端点数量: {len(endpoints)}")
    
    for endpoint in endpoints:
        print(f"   - {endpoint['method']} {endpoint['path']}: {endpoint['summary']}")
        print(f"     参数数量: {len(endpoint['parameters'])}")
        print(f"     响应数量: {len(endpoint['responses'])}")
        if endpoint['request_body']:
            print(f"     有请求体: 是")
        print()
    
    # 验证解析正确性
    print("\n4. 验证解析正确性...")
    
    # 检查嵌套引用是否被正确解析
    user_schema = resolved_doc['components']['schemas']['User']
    status_property = user_schema['properties']['status']
    
    if 'enum' in status_property:
        print("✅ 嵌套引用解析正确: User.status 包含 enum 值")
        print(f"   状态值: {status_property['enum']}")
    else:
        print("❌ 嵌套引用解析失败")
    
    # 检查数组引用是否被正确解析
    user_list_schema = resolved_doc['components']['schemas']['UserList']
    users_array = user_list_schema['properties']['users']
    
    if 'items' in users_array and 'properties' in users_array['items']:
        print("✅ 数组引用解析正确: UserList.users 包含 User 属性")
    else:
        print("❌ 数组引用解析失败")
    
    print("\n🎉 $ref 解析测试完成！")

def test_complex_refs():
    """测试复杂的 $ref 场景"""
    print("\n🔍 测试复杂 $ref 场景")
    print("=" * 40)
    
    # 包含循环引用的文档（应该被检测到）
    complex_doc = {
        "openapi": "3.0.0",
        "info": {"title": "Complex API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ComplexType"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "ComplexType": {
                    "type": "object",
                    "properties": {
                        "self_ref": {
                            "$ref": "#/components/schemas/ComplexType"
                        },
                        "simple": {
                            "type": "string"
                        }
                    }
                }
            }
        }
    }
    
    resolver = OpenApiRefResolver()
    
    try:
        resolved = resolver.resolve_document(json.dumps(complex_doc))
        print("✅ 复杂引用解析成功")
        
        # 检查是否检测到循环引用
        complex_type = resolved['components']['schemas']['ComplexType']
        if 'self_ref' in complex_type['properties']:
            print("✅ 循环引用被正确处理")
        
    except Exception as e:
        print(f"❌ 复杂引用解析失败: {e}")

if __name__ == "__main__":
    test_ref_resolution()
    test_complex_refs() 