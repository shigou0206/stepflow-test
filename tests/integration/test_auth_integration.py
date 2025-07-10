#!/usr/bin/env python3
"""
认证系统与 API 文档系统集成测试
演示两个系统如何协同工作
"""

import sqlite3
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

class AuthIntegrationTest:
    """认证系统集成测试"""
    
    def __init__(self, db_path: str = "test_gateway_with_auth.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def setup_database(self):
        """设置数据库"""
        print("🔧 设置包含认证功能的数据库...")
        with open('database/schema/stepflow_gateway.sql', 'r') as f:
            sql_content = f.read()
        try:
            self.cursor.executescript(sql_content)
            self.conn.commit()
            print("✅ 数据库设置完成！")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
    
    def test_api_document_registration_with_auth(self):
        """测试带认证配置的 API 文档注册"""
        print("\n📝 测试 API 文档注册与认证配置...")
        
        # 1. 准备 OpenAPI 文档
        openapi_content = {
            "openapi": "3.0.0",
            "info": {
                "title": "Payment API",
                "version": "1.0.0",
                "description": "Payment processing API"
            },
            "paths": {
                "/payments": {
                    "get": {
                        "summary": "List payments",
                        "security": [{"bearerAuth": []}]
                    },
                    "post": {
                        "summary": "Create payment",
                        "security": [{"bearerAuth": []}]
                    }
                },
                "/payments/{id}": {
                    "get": {
                        "summary": "Get payment by ID",
                        "security": [{"bearerAuth": []}]
                    }
                }
            }
        }
        
        # 2. 注册 OpenAPI 模板
        template_id = str(uuid.uuid4())
        self.cursor.execute('''
            INSERT INTO openapi_templates (id, name, content, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            template_id,
            'Payment API Template',
            json.dumps(openapi_content),
            'active',
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # 3. 创建 API 文档
        doc_id = str(uuid.uuid4())
        self.cursor.execute('''
            INSERT INTO api_documents (id, template_id, name, version, base_url, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            doc_id,
            template_id,
            'Payment API v1',
            '1.0.0',
            'https://api.payment.example.com',
            'active',
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # 4. 创建 API 端点
        endpoints = [
            ('/payments', 'GET', 'listPayments', 'List all payments'),
            ('/payments', 'POST', 'createPayment', 'Create a new payment'),
            ('/payments/{id}', 'GET', 'getPayment', 'Get payment by ID')
        ]
        
        endpoint_ids = []
        for path, method, operation_id, summary in endpoints:
            endpoint_id = str(uuid.uuid4())
            self.cursor.execute('''
                INSERT INTO api_endpoints (id, api_document_id, path, method, operation_id, summary, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                endpoint_id,
                doc_id,
                path,
                method,
                operation_id,
                summary,
                'active',
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            endpoint_ids.append(endpoint_id)
        
        # 5. 创建认证配置
        auth_config_id = str(uuid.uuid4())
        auth_config = {
            'token': 'encrypted_payment_token_123',
            'prefix': 'Bearer',
            'header_name': 'Authorization'
        }
        
        self.cursor.execute('''
            INSERT INTO api_auth_configs (id, api_document_id, auth_type, auth_config, is_required, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            auth_config_id,
            doc_id,
            'bearer',
            json.dumps(auth_config),
            1,
            'active',
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # 6. 创建认证凭据
        credential_id = str(uuid.uuid4())
        self.cursor.execute('''
            INSERT INTO auth_credentials (id, auth_config_id, credential_type, credential_key, credential_value, is_encrypted, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            credential_id,
            auth_config_id,
            'static',
            'payment_bearer_token',
            'encrypted_payment_token_value',
            1,
            'active',
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
        print(f"✅ API 文档注册完成！")
        print(f"   文档ID: {doc_id}")
        print(f"   端点数量: {len(endpoint_ids)}")
        print(f"   认证类型: Bearer Token")
        
        return doc_id, endpoint_ids, auth_config_id
    
    def test_api_call_with_authentication(self):
        """测试带认证的 API 调用"""
        print("\n🔐 测试带认证的 API 调用...")
        
        # 1. 模拟 API 调用请求
        request_data = {
            'path': '/payments',
            'method': 'GET',
            'headers': {
                'Content-Type': 'application/json',
                'User-Agent': 'StepFlow-Gateway/1.0.0'
            },
            'body': '',
            'query_params': {'limit': '10', 'status': 'completed'},
            'client_ip': '192.168.1.100'
        }
        
        # 2. 查找对应的端点
        self.cursor.execute('''
            SELECT e.id, e.api_document_id, e.path, e.method, e.summary
            FROM api_endpoints e
            WHERE e.path = ? AND e.method = ? AND e.status = 'active'
        ''', (request_data['path'], request_data['method']))
        
        endpoint = self.cursor.fetchone()
        if not endpoint:
            print("❌ 端点未找到")
            return
        
        endpoint_id = endpoint['id']
        api_document_id = endpoint['api_document_id']
        
        print(f"   找到端点: {endpoint['path']} {endpoint['method']}")
        print(f"   端点描述: {endpoint['summary']}")
        
        # 3. 获取认证配置
        self.cursor.execute('''
            SELECT id, auth_type, auth_config, is_required
            FROM api_auth_configs
            WHERE api_document_id = ? AND status = 'active'
        ''', (api_document_id,))
        
        auth_config_row = self.cursor.fetchone()
        if auth_config_row:
            auth_config = json.loads(auth_config_row['auth_config'])
            print(f"   认证类型: {auth_config_row['auth_type']}")
            print(f"   认证必需: {bool(auth_config_row['is_required'])}")
            
            # 4. 模拟认证过程
            auth_result = self.simulate_authentication(auth_config_row['auth_type'], auth_config)
            
            if auth_result['success']:
                # 5. 添加认证头到请求
                request_data['headers'].update(auth_result['auth_headers'])
                print(f"   认证成功: {auth_result['auth_headers']}")
                
                # 6. 模拟 API 调用
                response_data = self.simulate_api_call(request_data)
                
                # 7. 记录认证日志
                self.log_auth_attempt(auth_config_row['id'], 'success', 'static', 50, request_data['client_ip'])
                
                # 8. 记录 API 调用日志
                self.log_api_call(endpoint_id, request_data, response_data)
                
                print(f"   API 调用成功: {response_data['status_code']}")
                print(f"   响应时间: {response_data['response_time_ms']}ms")
            else:
                print(f"   ❌ 认证失败: {auth_result['error']}")
                self.log_auth_attempt(auth_config_row['id'], 'failed', 'static', 0, request_data['client_ip'], auth_result['error'])
        else:
            print("   ⚠️ 无需认证")
    
    def simulate_authentication(self, auth_type: str, auth_config: dict) -> dict:
        """模拟认证过程"""
        if auth_type == 'bearer':
            # 模拟 Bearer Token 认证
            token = auth_config.get('token', 'default_token')
            prefix = auth_config.get('prefix', 'Bearer')
            header_name = auth_config.get('header_name', 'Authorization')
            
            return {
                'success': True,
                'auth_headers': {
                    header_name: f"{prefix} {token}"
                }
            }
        elif auth_type == 'api_key':
            # 模拟 API Key 认证
            key_name = auth_config.get('key_name', 'X-API-Key')
            key_value = auth_config.get('key_value', 'default_key')
            
            return {
                'success': True,
                'auth_headers': {
                    key_name: key_value
                }
            }
        else:
            return {
                'success': False,
                'error': f'Unsupported auth type: {auth_type}'
            }
    
    def simulate_api_call(self, request_data: dict) -> dict:
        """模拟 API 调用"""
        # 模拟网络延迟
        time.sleep(0.1)
        
        return {
            'status_code': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Rate-Limit-Remaining': '999'
            },
            'body': {
                'payments': [
                    {'id': '1', 'amount': 100.00, 'status': 'completed'},
                    {'id': '2', 'amount': 250.50, 'status': 'pending'}
                ],
                'total': 2
            },
            'response_time_ms': 150
        }
    
    def log_auth_attempt(self, auth_config_id: str, status: str, method: str, response_time: int, client_ip: str, error_message: str = None):
        """记录认证尝试"""
        log_id = str(uuid.uuid4())
        self.cursor.execute('''
            INSERT INTO auth_logs (id, auth_config_id, auth_type, auth_status, auth_method, response_time_ms, client_ip, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_id,
            auth_config_id,
            'bearer',  # 从认证配置获取
            status,
            method,
            response_time,
            client_ip,
            error_message,
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def log_api_call(self, endpoint_id: str, request_data: dict, response_data: dict):
        """记录 API 调用"""
        log_id = str(uuid.uuid4())
        self.cursor.execute('''
            INSERT INTO api_call_logs (id, api_endpoint_id, request_method, request_url, request_headers, request_body, request_params, response_status_code, response_headers, response_body, response_time_ms, client_ip, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_id,
            endpoint_id,
            request_data['method'],
            f"https://api.payment.example.com{request_data['path']}",
            json.dumps(request_data['headers']),
            request_data['body'],
            json.dumps(request_data['query_params']),
            response_data['status_code'],
            json.dumps(response_data['headers']),
            json.dumps(response_data['body']),
            response_data['response_time_ms'],
            request_data['client_ip'],
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def test_oauth2_dynamic_auth(self):
        """测试 OAuth2 动态认证"""
        print("\n🔄 测试 OAuth2 动态认证...")
        
        # 1. 创建 OAuth2 认证配置
        oauth2_config = {
            'grant_type': 'client_credentials',
            'token_url': 'https://auth.example.com/oauth/token',
            'client_id': 'encrypted_client_id',
            'client_secret': 'encrypted_client_secret',
            'scope': 'read write',
            'token_type': 'Bearer'
        }
        
        # 2. 模拟 OAuth2 令牌获取
        oauth2_result = self.simulate_oauth2_token_request(oauth2_config)
        
        if oauth2_result['success']:
            print(f"   OAuth2 令牌获取成功")
            print(f"   令牌类型: {oauth2_result['token_type']}")
            print(f"   过期时间: {oauth2_result['expires_in']}秒")
            
            # 3. 缓存 OAuth2 令牌
            self.cache_oauth2_token(oauth2_result)
            
            # 4. 使用 OAuth2 令牌调用 API
            oauth2_request_data = {
                'path': '/payments',
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': {
                    'amount': 100.00,
                    'currency': 'USD'
                },
                'client_ip': '192.168.1.101'
            }
            
            # 添加 OAuth2 认证头
            oauth2_request_data['headers']['Authorization'] = f"Bearer {oauth2_result['access_token']}"
            
            print(f"   使用 OAuth2 令牌调用 API...")
            response = self.simulate_api_call(oauth2_request_data)
            print(f"   API 调用成功: {response['status_code']}")
        else:
            print(f"   ❌ OAuth2 令牌获取失败: {oauth2_result['error']}")
    
    def simulate_oauth2_token_request(self, config: dict) -> dict:
        """模拟 OAuth2 令牌请求"""
        # 模拟网络请求
        time.sleep(0.2)
        
        return {
            'success': True,
            'access_token': 'oauth2_access_token_123',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': config['scope']
        }
    
    def cache_oauth2_token(self, oauth2_result: dict):
        """缓存 OAuth2 令牌"""
        cache_id = str(uuid.uuid4())
        expires_at = datetime.now().timestamp() + oauth2_result['expires_in']
        
        self.cursor.execute('''
            INSERT INTO auth_cache (id, auth_config_id, cache_key, cache_value, cache_type, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            cache_id,
            'oauth2-config-id',  # 实际的认证配置ID
            'oauth2_token',
            json.dumps(oauth2_result),
            'token',
            datetime.fromtimestamp(expires_at).isoformat(),
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def show_integration_statistics(self):
        """显示集成统计信息"""
        print("\n📊 集成统计信息:")
        
        # 1. API 文档统计
        self.cursor.execute('SELECT COUNT(*) as count FROM api_documents')
        doc_count = self.cursor.fetchone()['count']
        
        # 2. 端点统计
        self.cursor.execute('SELECT COUNT(*) as count FROM api_endpoints')
        endpoint_count = self.cursor.fetchone()['count']
        
        # 3. 认证配置统计
        self.cursor.execute('SELECT COUNT(*) as count FROM api_auth_configs')
        auth_config_count = self.cursor.fetchone()['count']
        
        # 4. 认证日志统计
        self.cursor.execute('SELECT COUNT(*) as count FROM auth_logs')
        auth_log_count = self.cursor.fetchone()['count']
        
        # 5. API 调用日志统计
        self.cursor.execute('SELECT COUNT(*) as count FROM api_call_logs')
        api_log_count = self.cursor.fetchone()['count']
        
        print(f"   API 文档数量: {doc_count}")
        print(f"   API 端点数量: {endpoint_count}")
        print(f"   认证配置数量: {auth_config_count}")
        print(f"   认证日志数量: {auth_log_count}")
        print(f"   API 调用日志数量: {api_log_count}")
        
        # 6. 认证类型分布
        self.cursor.execute('''
            SELECT auth_type, COUNT(*) as count
            FROM api_auth_configs
            GROUP BY auth_type
        ''')
        auth_types = self.cursor.fetchall()
        print(f"\n   认证类型分布:")
        for auth_type in auth_types:
            print(f"     {auth_type['auth_type']}: {auth_type['count']}")
        
        # 7. 认证成功率
        self.cursor.execute('''
            SELECT 
                auth_status,
                COUNT(*) as count
            FROM auth_logs
            GROUP BY auth_status
        ''')
        auth_stats = self.cursor.fetchall()
        print(f"\n   认证状态统计:")
        for stat in auth_stats:
            print(f"     {stat['auth_status']}: {stat['count']}")
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

def main():
    """主函数"""
    print("🚀 StepFlow Gateway 认证系统集成测试")
    print("=" * 60)
    
    try:
        # 创建测试实例
        test = AuthIntegrationTest()
        
        # 设置数据库
        test.setup_database()
        
        # 测试 API 文档注册与认证配置
        doc_id, endpoint_ids, auth_config_id = test.test_api_document_registration_with_auth()
        
        # 测试带认证的 API 调用
        test.test_api_call_with_authentication()
        
        # 测试 OAuth2 动态认证
        test.test_oauth2_dynamic_auth()
        
        # 显示统计信息
        test.show_integration_statistics()
        
        # 关闭连接
        test.close()
        
        print("\n🎉 认证系统集成测试完成！")
        print("📁 数据库文件: test_gateway_with_auth.db")
        print("💡 可以使用 SQLite 工具查看数据:")
        print("   sqlite3 test_gateway_with_auth.db")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    main()