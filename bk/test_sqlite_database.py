#!/usr/bin/env python3
"""
StepFlow Gateway SQLite 数据库测试脚本
测试数据库的创建、插入和查询功能
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

class SQLiteDatabaseTester:
    """SQLite 数据库测试器"""
    
    def __init__(self, db_path: str = "stepflow_gateway.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """连接到数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            print(f"✅ 成功连接到数据库: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ 连接数据库失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("🔒 数据库连接已关闭")
    
    def init_database(self):
        """初始化数据库"""
        try:
            with open('database_init_sqlite.sql', 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            self.conn.executescript(sql_script)
            self.conn.commit()
            print("✅ 数据库初始化成功")
            return True
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False
    
    def test_insert_template(self):
        """测试插入 OpenAPI 模板"""
        try:
            template_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            template_data = {
                'id': template_id,
                'name': 'Test API Template',
                'description': '测试用的 API 模板',
                'version': '1.0.0',
                'category': '测试',
                'tags': json.dumps(['test', 'api', 'template']),
                'template_content': '''
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
  description: 测试 API
paths:
  /test:
    get:
      summary: Test endpoint
      operationId: testGet
      responses:
        "200":
          description: Success
''',
                'content_type': 'yaml',
                'is_public': 1,
                'created_at': now,
                'updated_at': now
            }
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO openapi_templates 
                (id, name, description, version, category, tags, template_content, 
                 content_type, is_public, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template_data['id'], template_data['name'], template_data['description'],
                template_data['version'], template_data['category'], template_data['tags'],
                template_data['template_content'], template_data['content_type'],
                template_data['is_public'], template_data['created_at'], template_data['updated_at']
            ))
            
            self.conn.commit()
            print(f"✅ 成功插入模板: {template_data['name']}")
            return template_id
        except Exception as e:
            print(f"❌ 插入模板失败: {e}")
            return None
    
    def test_insert_api_document(self, template_id: Optional[str] = None):
        """测试插入 API 文档"""
        try:
            doc_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            doc_data = {
                'id': doc_id,
                'template_id': template_id,
                'name': 'Test API Document',
                'description': '测试用的 API 文档',
                'version': '1.0.0',
                'base_url': 'https://api.example.com/v1',
                'parsed_spec': json.dumps({
                    'openapi': '3.0.0',
                    'info': {'title': 'Test API', 'version': '1.0.0'},
                    'paths': {}
                }),
                'original_content': 'openapi: 3.0.0\ninfo:\n  title: Test API\n  version: 1.0.0',
                'content_type': 'yaml',
                'created_at': now,
                'updated_at': now
            }
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO api_documents 
                (id, template_id, name, description, version, base_url, parsed_spec, 
                 original_content, content_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                doc_data['id'], doc_data['template_id'], doc_data['name'],
                doc_data['description'], doc_data['version'], doc_data['base_url'],
                doc_data['parsed_spec'], doc_data['original_content'],
                doc_data['content_type'], doc_data['created_at'], doc_data['updated_at']
            ))
            
            self.conn.commit()
            print(f"✅ 成功插入 API 文档: {doc_data['name']}")
            return doc_id
        except Exception as e:
            print(f"❌ 插入 API 文档失败: {e}")
            return None
    
    def test_insert_endpoints(self, api_document_id: str):
        """测试插入 API 端点"""
        try:
            now = datetime.now().isoformat()
            endpoints = [
                {
                    'id': str(uuid.uuid4()),
                    'api_document_id': api_document_id,
                    'path': '/users',
                    'method': 'GET',
                    'operation_id': 'getUsers',
                    'summary': 'Get users',
                    'description': '获取用户列表',
                    'tags': json.dumps(['users', 'list']),
                    'status': 'active',
                    'created_at': now,
                    'updated_at': now
                },
                {
                    'id': str(uuid.uuid4()),
                    'api_document_id': api_document_id,
                    'path': '/users/{userId}',
                    'method': 'GET',
                    'operation_id': 'getUserById',
                    'summary': 'Get user by ID',
                    'description': '根据ID获取用户',
                    'tags': json.dumps(['users', 'detail']),
                    'status': 'active',
                    'created_at': now,
                    'updated_at': now
                }
            ]
            
            cursor = self.conn.cursor()
            for endpoint in endpoints:
                cursor.execute('''
                    INSERT INTO api_endpoints 
                    (id, api_document_id, path, method, operation_id, summary, description, 
                     tags, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    endpoint['id'], endpoint['api_document_id'], endpoint['path'],
                    endpoint['method'], endpoint['operation_id'], endpoint['summary'],
                    endpoint['description'], endpoint['tags'], endpoint['status'],
                    endpoint['created_at'], endpoint['updated_at']
                ))
            
            self.conn.commit()
            print(f"✅ 成功插入 {len(endpoints)} 个端点")
            return [e['id'] for e in endpoints]
        except Exception as e:
            print(f"❌ 插入端点失败: {e}")
            return []
    
    def test_query_endpoints(self):
        """测试查询端点"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    e.id, e.path, e.method, e.operation_id, e.summary,
                    d.name as api_name, d.base_url,
                    e.call_count, e.success_count, e.error_count
                FROM api_endpoints e
                JOIN api_documents d ON e.api_document_id = d.id
                WHERE e.status = 'active'
                ORDER BY e.created_at DESC
            ''')
            
            endpoints = cursor.fetchall()
            print(f"\n📋 查询到 {len(endpoints)} 个活跃端点:")
            print("-" * 80)
            
            for endpoint in endpoints:
                print(f"ID: {endpoint['id']}")
                print(f"路径: {endpoint['method']} {endpoint['path']}")
                print(f"操作: {endpoint['operation_id']}")
                print(f"摘要: {endpoint['summary']}")
                print(f"API: {endpoint['api_name']} ({endpoint['base_url']})")
                print(f"统计: 调用 {endpoint['call_count']} 次, 成功 {endpoint['success_count']} 次, 错误 {endpoint['error_count']} 次")
                print("-" * 40)
            
            return endpoints
        except Exception as e:
            print(f"❌ 查询端点失败: {e}")
            return []
    
    def test_query_resources_view(self):
        """测试查询资源视图"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    endpoint_id, path, method, operation_id, summary,
                    api_name, api_version, base_url,
                    call_count, success_count, error_count, reference_count
                FROM api_endpoint_resources
                ORDER BY call_count DESC
            ''')
            
            resources = cursor.fetchall()
            print(f"\n🔍 资源视图查询结果 ({len(resources)} 条):")
            print("-" * 80)
            
            for resource in resources:
                success_rate = (resource['success_count'] / resource['call_count'] * 100) if resource['call_count'] > 0 else 0
                print(f"{resource['method']} {resource['path']} - {resource['summary']}")
                print(f"  API: {resource['api_name']} v{resource['api_version']}")
                print(f"  调用: {resource['call_count']} 次, 成功率: {success_rate:.1f}%")
                print(f"  引用: {resource['reference_count']} 次")
                print()
            
            return resources
        except Exception as e:
            print(f"❌ 查询资源视图失败: {e}")
            return []
    
    def test_insert_call_log(self, endpoint_id: str):
        """测试插入调用日志"""
        try:
            log_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            log_data = {
                'id': log_id,
                'api_endpoint_id': endpoint_id,
                'request_method': 'GET',
                'request_url': 'https://api.example.com/v1/users?limit=10',
                'request_headers': json.dumps({'Content-Type': 'application/json'}),
                'request_params': json.dumps({'limit': '10'}),
                'response_status_code': 200,
                'response_headers': json.dumps({'Content-Type': 'application/json'}),
                'response_body': json.dumps({'users': [], 'total': 0}),
                'response_time_ms': 150,
                'request_size_bytes': 0,
                'response_size_bytes': 25,
                'created_at': now
            }
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO api_call_logs 
                (id, api_endpoint_id, request_method, request_url, request_headers,
                 request_params, response_status_code, response_headers, response_body,
                 response_time_ms, request_size_bytes, response_size_bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_data['id'], log_data['api_endpoint_id'], log_data['request_method'],
                log_data['request_url'], log_data['request_headers'], log_data['request_params'],
                log_data['response_status_code'], log_data['response_headers'],
                log_data['response_body'], log_data['response_time_ms'],
                log_data['request_size_bytes'], log_data['response_size_bytes'],
                log_data['created_at']
            ))
            
            self.conn.commit()
            print(f"✅ 成功插入调用日志: {log_data['request_method']} {log_data['request_url']}")
            return log_id
        except Exception as e:
            print(f"❌ 插入调用日志失败: {e}")
            return None
    
    def test_database_stats(self):
        """测试数据库统计"""
        try:
            cursor = self.conn.cursor()
            
            # 统计各表记录数
            tables = ['openapi_templates', 'api_documents', 'api_endpoints', 
                     'resource_references', 'api_call_logs', 'api_health_checks']
            
            print("\n📊 数据库统计信息:")
            print("-" * 40)
            
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                count = cursor.fetchone()['count']
                print(f"{table}: {count} 条记录")
            
            # 统计活跃端点
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_endpoints,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_endpoints,
                    SUM(call_count) as total_calls,
                    SUM(success_count) as total_success,
                    SUM(error_count) as total_errors
                FROM api_endpoints
            ''')
            
            stats = cursor.fetchone()
            print(f"\n端点统计:")
            print(f"  总端点数: {stats['total_endpoints']}")
            print(f"  活跃端点: {stats['active_endpoints']}")
            print(f"  总调用数: {stats['total_calls']}")
            print(f"  成功调用: {stats['total_success']}")
            print(f"  错误调用: {stats['total_errors']}")
            
            if stats['total_calls'] > 0:
                success_rate = (stats['total_success'] / stats['total_calls']) * 100
                print(f"  成功率: {success_rate:.1f}%")
            
            return True
        except Exception as e:
            print(f"❌ 统计失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始 SQLite 数据库测试")
        print("=" * 50)
        
        # 连接数据库
        if not self.connect():
            return False
        
        try:
            # 初始化数据库
            if not self.init_database():
                return False
            
            # 测试插入模板
            template_id = self.test_insert_template()
            
            # 测试插入 API 文档
            doc_id = self.test_insert_api_document(template_id)
            
            # 测试插入端点
            if doc_id:
                endpoint_ids = self.test_insert_endpoints(doc_id)
                
                # 测试插入调用日志
                if endpoint_ids:
                    self.test_insert_call_log(endpoint_ids[0])
            
            # 测试查询
            self.test_query_endpoints()
            self.test_query_resources_view()
            
            # 测试统计
            self.test_database_stats()
            
            print("\n🎉 所有测试完成!")
            return True
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            return False
        finally:
            self.close()

def main():
    """主函数"""
    tester = SQLiteDatabaseTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 数据库测试全部通过!")
    else:
        print("\n❌ 数据库测试失败!")

if __name__ == "__main__":
    main() 