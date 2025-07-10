#!/usr/bin/env python3
"""
简化版数据库测试脚本
快速验证 StepFlow Gateway 的核心功能
"""

import sqlite3
import json
from datetime import datetime

def create_simple_database():
    """创建简化版数据库"""
    print("🔧 创建简化版数据库...")
    
    conn = sqlite3.connect('simple_gateway.db')
    cursor = conn.cursor()
    
    # 读取并执行 SQL 文件
    with open('simple_database_init.sql', 'r') as f:
        sql_content = f.read()
    
    # 分割 SQL 语句并执行
    statements = sql_content.split(';')
    for statement in statements:
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
            except sqlite3.OperationalError as e:
                if "already exists" not in str(e):
                    print(f"执行语句时出错: {e}")
    
    conn.commit()
    print("✅ 数据库创建完成！")

def test_basic_operations():
    """测试基本操作"""
    print("\n🧪 测试基本操作...")
    
    conn = sqlite3.connect('simple_gateway.db')
    cursor = conn.cursor()
    
    # 1. 查看模板
    print("\n1. OpenAPI 模板:")
    cursor.execute('SELECT id, name, status FROM openapi_templates')
    templates = cursor.fetchall()
    for template in templates:
        print(f"   ID: {template[0]}, 名称: {template[1]}, 状态: {template[2]}")
    
    # 2. 查看端点
    print("\n2. API 端点:")
    cursor.execute('SELECT id, path, method, summary FROM api_endpoints')
    endpoints = cursor.fetchall()
    for endpoint in endpoints:
        print(f"   ID: {endpoint[0]}, 路径: {endpoint[1]}, 方法: {endpoint[2]}, 描述: {endpoint[3]}")
    
    # 3. 查看日志
    print("\n3. HTTP 请求日志:")
    cursor.execute('SELECT request_method, request_url, response_status_code, response_time_ms FROM api_call_logs')
    logs = cursor.fetchall()
    for log in logs:
        print(f"   {log[0]} {log[1]} -> {log[2]} ({log[3]}ms)")
    
    # 4. 查看视图
    print("\n4. 端点统计视图:")
    cursor.execute('SELECT path, method, template_name, call_count, avg_response_time FROM endpoint_summary')
    summary = cursor.fetchall()
    for item in summary:
        print(f"   {item[1]} {item[0]} ({item[2]}) - 调用次数: {item[3]}, 平均响应时间: {item[4]:.1f}ms")
    
    conn.close()

def test_add_new_template():
    """测试添加新模板"""
    print("\n➕ 测试添加新模板...")
    
    conn = sqlite3.connect('simple_gateway.db')
    cursor = conn.cursor()
    
    # 添加新模板
    new_template = {
        'id': 'template-3',
        'name': 'Weather API',
        'content': json.dumps({
            'openapi': '3.0.0',
            'info': {'title': 'Weather API', 'version': '1.0.0'},
            'paths': {
                '/weather': {
                    'get': {'summary': 'Get weather information'}
                }
            }
        }),
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    cursor.execute('''
        INSERT INTO openapi_templates (id, name, content, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (new_template['id'], new_template['name'], new_template['content'], 
          new_template['status'], new_template['created_at'], new_template['updated_at']))
    
    # 添加对应的端点
    new_endpoint = {
        'id': 'endpoint-4',
        'template_id': 'template-3',
        'path': '/weather',
        'method': 'GET',
        'base_url': 'https://weather-api.example.com',
        'operation_id': 'getWeather',
        'summary': 'Get current weather',
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    cursor.execute('''
        INSERT INTO api_endpoints (id, template_id, path, method, base_url, operation_id, summary, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (new_endpoint['id'], new_endpoint['template_id'], new_endpoint['path'], 
          new_endpoint['method'], new_endpoint['base_url'], new_endpoint['operation_id'],
          new_endpoint['summary'], new_endpoint['status'], new_endpoint['created_at'], new_endpoint['updated_at']))
    
    conn.commit()
    print("✅ 新模板和端点添加成功！")
    
    # 验证添加结果
    cursor.execute('SELECT COUNT(*) FROM openapi_templates')
    template_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM api_endpoints')
    endpoint_count = cursor.fetchone()[0]
    
    print(f"   模板总数: {template_count}")
    print(f"   端点总数: {endpoint_count}")
    
    conn.close()

def test_log_http_request():
    """测试记录 HTTP 请求"""
    print("\n📝 测试记录 HTTP 请求...")
    
    conn = sqlite3.connect('simple_gateway.db')
    cursor = conn.cursor()
    
    # 模拟 HTTP 请求日志
    request_log = {
        'id': 'log-4',
        'endpoint_id': 'endpoint-4',
        'request_method': 'GET',
        'request_url': 'https://weather-api.example.com/weather?city=Beijing',
        'request_headers': json.dumps({
            'Content-Type': 'application/json',
            'User-Agent': 'StepFlow-Gateway/1.0.0'
        }),
        'request_body': '',
        'response_status_code': 200,
        'response_headers': json.dumps({
            'Content-Type': 'application/json',
            'Cache-Control': 'max-age=300'
        }),
        'response_body': json.dumps({
            'city': 'Beijing',
            'temperature': 25,
            'condition': 'sunny'
        }),
        'response_time_ms': 180,
        'error_message': None,
        'client_ip': '192.168.1.102',
        'created_at': datetime.now().isoformat()
    }
    
    cursor.execute('''
        INSERT INTO api_call_logs 
        (id, endpoint_id, request_method, request_url, request_headers, request_body,
         response_status_code, response_headers, response_body, response_time_ms,
         error_message, client_ip, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (request_log['id'], request_log['endpoint_id'], request_log['request_method'],
          request_log['request_url'], request_log['request_headers'], request_log['request_body'],
          request_log['response_status_code'], request_log['response_headers'], request_log['response_body'],
          request_log['response_time_ms'], request_log['error_message'], request_log['client_ip'],
          request_log['created_at']))
    
    conn.commit()
    print("✅ HTTP 请求日志记录成功！")
    
    # 验证日志记录
    cursor.execute('SELECT COUNT(*) FROM api_call_logs')
    log_count = cursor.fetchone()[0]
    print(f"   日志总数: {log_count}")
    
    # 查看最新的日志
    cursor.execute('''
        SELECT request_method, request_url, response_status_code, response_time_ms, client_ip
        FROM api_call_logs ORDER BY created_at DESC LIMIT 1
    ''')
    latest_log = cursor.fetchone()
    print(f"   最新日志: {latest_log[0]} {latest_log[1]} -> {latest_log[2]} ({latest_log[3]}ms) from {latest_log[4]}")
    
    conn.close()

def test_query_examples():
    """测试查询示例"""
    print("\n🔍 测试查询示例...")
    
    conn = sqlite3.connect('simple_gateway.db')
    cursor = conn.cursor()
    
    # 1. 查询成功的请求
    print("\n1. 成功的请求 (状态码 200-299):")
    cursor.execute('''
        SELECT request_method, request_url, response_status_code, response_time_ms
        FROM api_call_logs 
        WHERE response_status_code BETWEEN 200 AND 299
        ORDER BY created_at DESC
    ''')
    success_logs = cursor.fetchall()
    for log in success_logs:
        print(f"   {log[0]} {log[1]} -> {log[2]} ({log[3]}ms)")
    
    # 2. 查询失败的请求
    print("\n2. 失败的请求 (状态码 >= 400):")
    cursor.execute('''
        SELECT request_method, request_url, response_status_code, error_message
        FROM api_call_logs 
        WHERE response_status_code >= 400
        ORDER BY created_at DESC
    ''')
    error_logs = cursor.fetchall()
    for log in error_logs:
        print(f"   {log[0]} {log[1]} -> {log[2]} (错误: {log[3] or '无'})")
    
    # 3. 查询慢请求 (>100ms)
    print("\n3. 慢请求 (>100ms):")
    cursor.execute('''
        SELECT request_method, request_url, response_time_ms
        FROM api_call_logs 
        WHERE response_time_ms > 100
        ORDER BY response_time_ms DESC
    ''')
    slow_logs = cursor.fetchall()
    for log in slow_logs:
        print(f"   {log[0]} {log[1]} ({log[2]}ms)")
    
    # 4. 统计每个端点的调用次数
    print("\n4. 端点调用统计:")
    cursor.execute('''
        SELECT e.path, e.method, COUNT(l.id) as call_count, AVG(l.response_time_ms) as avg_time
        FROM api_endpoints e
        LEFT JOIN api_call_logs l ON e.id = l.endpoint_id
        GROUP BY e.id
        ORDER BY call_count DESC
    ''')
    endpoint_stats = cursor.fetchall()
    for stat in endpoint_stats:
        print(f"   {stat[1]} {stat[0]} - 调用次数: {stat[2]}, 平均时间: {stat[3]:.1f}ms")
    
    conn.close()

def main():
    """主函数"""
    print("🚀 StepFlow Gateway 简化版数据库测试")
    print("=" * 50)
    
    try:
        # 创建数据库
        create_simple_database()
        
        # 测试基本操作
        test_basic_operations()
        
        # 测试添加新模板
        test_add_new_template()
        
        # 测试记录 HTTP 请求
        test_log_http_request()
        
        # 测试查询示例
        test_query_examples()
        
        print("\n🎉 所有测试完成！")
        print("📁 数据库文件: simple_gateway.db")
        print("💡 可以使用 SQLite 工具查看数据:")
        print("   sqlite3 simple_gateway.db")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    main() 