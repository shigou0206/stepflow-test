#!/usr/bin/env python3
"""
测试 HTTP 请求完整信息记录功能
演示如何记录和分析完整的 HTTP 请求信息
"""

import sqlite3
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

class HTTPRequestLogger:
    """HTTP 请求日志记录器"""
    
    def __init__(self, db_path: str = "stepflow_gateway.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def log_request(self, 
                   api_endpoint_id: str,
                   request_data: Dict[str, Any],
                   response_data: Dict[str, Any],
                   client_info: Optional[Dict[str, str]] = None,
                   resource_reference_id: Optional[str] = None) -> str:
        """记录完整的 HTTP 请求信息"""
        
        # 计算响应时间
        start_time = request_data.get('start_time', time.time())
        response_time = int((time.time() - start_time) * 1000)
        
        # 计算请求和响应大小
        request_body = request_data.get('body', '')
        response_body = response_data.get('body', '')
        request_size = len(str(request_body).encode('utf-8'))
        response_size = len(str(response_body).encode('utf-8'))
        
        # 生成日志ID
        log_id = str(uuid.uuid4())
        
        # 准备日志数据
        log_data = {
            'id': log_id,
            'api_endpoint_id': api_endpoint_id,
            'resource_reference_id': resource_reference_id,
            
            # 请求信息
            'request_method': request_data['method'],
            'request_url': request_data['url'],
            'request_headers': json.dumps(request_data.get('headers', {})),
            'request_body': str(request_body),
            'request_params': json.dumps({
                'query': request_data.get('query_params', {}),
                'path': request_data.get('path_params', {})
            }),
            
            # 响应信息
            'response_status_code': response_data['status_code'],
            'response_headers': json.dumps(response_data.get('headers', {})),
            'response_body': str(response_body),
            
            # 性能信息
            'response_time_ms': response_time,
            'request_size_bytes': request_size,
            'response_size_bytes': response_size,
            
            # 错误信息
            'error_message': response_data.get('error_message'),
            'error_type': response_data.get('error_type'),
            
            # 客户端信息
            'client_ip': client_info.get('ip') if client_info else None,
            'user_agent': client_info.get('user_agent') if client_info else None,
            
            # 时间信息
            'created_at': datetime.now().isoformat()
        }
        
        # 插入数据库
        self.cursor.execute('''
            INSERT INTO api_call_logs 
            (id, api_endpoint_id, resource_reference_id, request_method, request_url,
             request_headers, request_body, request_params, response_status_code,
             response_headers, response_body, response_time_ms, request_size_bytes,
             response_size_bytes, error_message, error_type, client_ip, user_agent, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_data['id'], log_data['api_endpoint_id'], log_data['resource_reference_id'],
            log_data['request_method'], log_data['request_url'], log_data['request_headers'],
            log_data['request_body'], log_data['request_params'], log_data['response_status_code'],
            log_data['response_headers'], log_data['response_body'], log_data['response_time_ms'],
            log_data['request_size_bytes'], log_data['response_size_bytes'], log_data['error_message'],
            log_data['error_type'], log_data['client_ip'], log_data['user_agent'], log_data['created_at']
        ))
        
        self.conn.commit()
        return log_id
    
    def get_request_log(self, log_id: str) -> Optional[Dict[str, Any]]:
        """获取单个请求日志"""
        self.cursor.execute('''
            SELECT * FROM api_call_logs WHERE id = ?
        ''', (log_id,))
        
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_performance_stats(self, endpoint_id: str, days: int = 7) -> Dict[str, Any]:
        """获取性能统计"""
        self.cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                AVG(response_time_ms) as avg_response_time,
                MAX(response_time_ms) as max_response_time,
                MIN(response_time_ms) as min_response_time,
                SUM(request_size_bytes) as total_request_size,
                SUM(response_size_bytes) as total_response_size,
                SUM(CASE WHEN response_status_code BETWEEN 200 AND 299 THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN response_status_code >= 400 THEN 1 ELSE 0 END) as error_count
            FROM api_call_logs 
            WHERE api_endpoint_id = ? 
            AND created_at > datetime('now', '-{} days')
        '''.format(days), (endpoint_id,))
        
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return {}
    
    def get_error_analysis(self, days: int = 1) -> list:
        """获取错误分析"""
        self.cursor.execute('''
            SELECT 
                error_type,
                COUNT(*) as error_count,
                AVG(response_time_ms) as avg_response_time,
                GROUP_CONCAT(DISTINCT response_status_code) as status_codes
            FROM api_call_logs 
            WHERE error_type IS NOT NULL
            AND created_at > datetime('now', '-{} days')
            GROUP BY error_type
            ORDER BY error_count DESC
        '''.format(days))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_slow_requests(self, threshold_ms: int = 1000, limit: int = 10) -> list:
        """获取慢请求"""
        self.cursor.execute('''
            SELECT 
                request_method,
                request_url,
                response_time_ms,
                response_status_code,
                created_at
            FROM api_call_logs 
            WHERE response_time_ms > ?
            ORDER BY response_time_ms DESC
            LIMIT ?
        ''', (threshold_ms, limit))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

def simulate_http_requests():
    """模拟 HTTP 请求并记录日志"""
    
    # 初始化日志记录器
    logger = HTTPRequestLogger()
    
    # 模拟的 API 端点ID
    endpoint_id = "endpoint-12345"
    
    # 模拟成功的 GET 请求
    print("=== 模拟成功的 GET 请求 ===")
    request_data = {
        'method': 'GET',
        'url': 'https://api.example.com/v1/users?limit=10&page=1',
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
            'User-Agent': 'StepFlow-Gateway/1.0.0',
            'Accept': 'application/json',
            'X-Request-ID': 'req-12345-67890'
        },
        'query_params': {'limit': '10', 'page': '1'},
        'path_params': {},
        'body': '',
        'start_time': time.time()
    }
    
    response_data = {
        'status_code': 200,
        'headers': {
            'Content-Type': 'application/json; charset=utf-8',
            'Content-Length': '1024',
            'Cache-Control': 'no-cache',
            'X-Rate-Limit-Remaining': '999',
            'X-Request-ID': 'req-12345-67890'
        },
        'body': {
            'success': True,
            'data': [
                {'id': '1', 'name': 'John Doe', 'email': 'john@example.com'},
                {'id': '2', 'name': 'Jane Smith', 'email': 'jane@example.com'}
            ],
            'meta': {'total': 2, 'page': 1, 'limit': 10}
        }
    }
    
    client_info = {
        'ip': '192.168.1.100',
        'user_agent': 'StepFlow-Gateway/1.0.0'
    }
    
    log_id = logger.log_request(endpoint_id, request_data, response_data, client_info)
    print(f"记录成功请求日志: {log_id}")
    
    # 模拟失败的 POST 请求
    print("\n=== 模拟失败的 POST 请求 ===")
    request_data = {
        'method': 'POST',
        'url': 'https://api.example.com/v1/users',
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer invalid-token',
            'User-Agent': 'StepFlow-Gateway/1.0.0'
        },
        'query_params': {},
        'path_params': {},
        'body': {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'secret123'
        },
        'start_time': time.time()
    }
    
    response_data = {
        'status_code': 401,
        'headers': {
            'Content-Type': 'application/json',
            'WWW-Authenticate': 'Bearer'
        },
        'body': {
            'error': 'Unauthorized',
            'message': 'Invalid or expired token'
        },
        'error_message': 'Authentication failed: Invalid token',
        'error_type': 'authentication'
    }
    
    log_id = logger.log_request(endpoint_id, request_data, response_data, client_info)
    print(f"记录失败请求日志: {log_id}")
    
    # 模拟超时的请求
    print("\n=== 模拟超时的请求 ===")
    request_data = {
        'method': 'GET',
        'url': 'https://api.example.com/v1/slow-endpoint',
        'headers': {
            'Content-Type': 'application/json',
            'User-Agent': 'StepFlow-Gateway/1.0.0'
        },
        'query_params': {},
        'path_params': {},
        'body': '',
        'start_time': time.time() - 35  # 35秒前开始
    }
    
    response_data = {
        'status_code': 0,  # 没有响应
        'headers': {},
        'body': '',
        'error_message': 'Connection timeout after 30 seconds',
        'error_type': 'timeout'
    }
    
    log_id = logger.log_request(endpoint_id, request_data, response_data, client_info)
    print(f"记录超时请求日志: {log_id}")
    
    # 模拟验证错误的请求
    print("\n=== 模拟验证错误的请求 ===")
    request_data = {
        'method': 'PUT',
        'url': 'https://api.example.com/v1/users/123',
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer valid-token',
            'User-Agent': 'StepFlow-Gateway/1.0.0'
        },
        'query_params': {},
        'path_params': {'userId': '123'},
        'body': {
            'email': 'invalid-email',  # 无效的邮箱格式
            'age': -5  # 无效的年龄
        },
        'start_time': time.time()
    }
    
    response_data = {
        'status_code': 400,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': {
            'error': 'Validation Error',
            'message': 'Invalid input data',
            'details': [
                {'field': 'email', 'message': 'Invalid email format'},
                {'field': 'age', 'message': 'Age must be positive'}
            ]
        },
        'error_message': 'Validation failed: Invalid input data',
        'error_type': 'validation'
    }
    
    log_id = logger.log_request(endpoint_id, request_data, response_data, client_info)
    print(f"记录验证错误日志: {log_id}")
    
    return logger

def analyze_logs(logger: HTTPRequestLogger):
    """分析记录的日志"""
    
    endpoint_id = "endpoint-12345"
    
    print("\n" + "="*50)
    print("日志分析结果")
    print("="*50)
    
    # 获取性能统计
    print("\n1. 性能统计 (最近7天):")
    stats = logger.get_performance_stats(endpoint_id, 7)
    if stats:
        print(f"   总请求数: {stats['total_requests']}")
        print(f"   平均响应时间: {stats['avg_response_time']:.2f}ms")
        print(f"   最大响应时间: {stats['max_response_time']}ms")
        print(f"   最小响应时间: {stats['min_response_time']}ms")
        print(f"   成功请求数: {stats['success_count']}")
        print(f"   错误请求数: {stats['error_count']}")
        print(f"   总请求大小: {stats['total_request_size']} bytes")
        print(f"   总响应大小: {stats['total_response_size']} bytes")
    
    # 获取错误分析
    print("\n2. 错误分析 (最近1天):")
    errors = logger.get_error_analysis(1)
    for error in errors:
        print(f"   错误类型: {error['error_type']}")
        print(f"   错误次数: {error['error_count']}")
        print(f"   平均响应时间: {error['avg_response_time']:.2f}ms")
        print(f"   状态码: {error['status_codes']}")
        print()
    
    # 获取慢请求
    print("\n3. 慢请求 (>1000ms):")
    slow_requests = logger.get_slow_requests(1000, 5)
    for req in slow_requests:
        print(f"   方法: {req['request_method']}")
        print(f"   URL: {req['request_url']}")
        print(f"   响应时间: {req['response_time_ms']}ms")
        print(f"   状态码: {req['response_status_code']}")
        print(f"   时间: {req['created_at']}")
        print()

def display_sample_log(logger: HTTPRequestLogger):
    """显示示例日志记录"""
    
    print("\n" + "="*50)
    print("示例日志记录详情")
    print("="*50)
    
    # 获取第一条日志记录
    logger.cursor.execute('SELECT * FROM api_call_logs LIMIT 1')
    row = logger.cursor.fetchone()
    
    if row:
        log = dict(row)
        print(f"\n日志ID: {log['id']}")
        print(f"API端点ID: {log['api_endpoint_id']}")
        print(f"请求方法: {log['request_method']}")
        print(f"请求URL: {log['request_url']}")
        print(f"响应状态码: {log['response_status_code']}")
        print(f"响应时间: {log['response_time_ms']}ms")
        print(f"客户端IP: {log['client_ip']}")
        print(f"创建时间: {log['created_at']}")
        
        print(f"\n请求头:")
        headers = json.loads(log['request_headers'])
        for key, value in headers.items():
            if key.lower() in ['authorization', 'x-api-key']:
                print(f"  {key}: ***REDACTED***")
            else:
                print(f"  {key}: {value}")
        
        print(f"\n请求体:")
        if log['request_body']:
            try:
                body = json.loads(log['request_body'])
                print(json.dumps(body, indent=2, ensure_ascii=False))
            except:
                print(log['request_body'])
        else:
            print("  (空)")
        
        print(f"\n响应体:")
        if log['response_body']:
            try:
                body = json.loads(log['response_body'])
                print(json.dumps(body, indent=2, ensure_ascii=False))
            except:
                print(log['response_body'])
        else:
            print("  (空)")

def main():
    """主函数"""
    print("StepFlow Gateway HTTP 请求日志记录测试")
    print("="*50)
    
    # 模拟 HTTP 请求并记录日志
    logger = simulate_http_requests()
    
    # 分析日志
    analyze_logs(logger)
    
    # 显示示例日志详情
    display_sample_log(logger)
    
    # 关闭数据库连接
    logger.close()
    
    print("\n测试完成！")
    print("数据库文件: stepflow_gateway.db")
    print("可以使用 SQLite 工具查看完整的日志数据")

if __name__ == "__main__":
    main() 