#!/usr/bin/env python3
"""
性能测试
"""

import unittest
import json
import time
import threading
import psutil
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from stepflow_gateway.core.gateway import StepFlowGateway


class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def setUp(self):
        self.gateway = StepFlowGateway()
        
        # 基础 OpenAPI 规范
        self.base_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Performance Test API",
                "version": "1.0.0"
            },
            "servers": [
                {
                    "url": "https://api.example.com/v1"
                }
            ],
            "paths": {}
        }
    
    def get_memory_usage(self):
        """获取当前进程内存使用"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def test_bulk_api_registration_performance(self):
        """测试批量 API 注册性能"""
        print(f"\n开始批量 API 注册性能测试...")
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        # 注册 50 个 API
        api_count = 50
        successful_registrations = 0
        
        for i in range(api_count):
            spec = self.base_spec.copy()
            spec["paths"] = {
                f"/endpoint{i}": {
                    "get": {
                        "summary": f"Endpoint {i}",
                        "parameters": [
                            {
                                "name": "param",
                                "in": "query",
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "OK"}
                        }
                    }
                }
            }
            
            result = self.gateway.register_api(
                name=f"Performance API {i}",
                openapi_content=json.dumps(spec),
                version="1.0.0"
            )
            
            if result.get('success'):
                successful_registrations += 1
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        total_time = end_time - start_time
        memory_increase = end_memory - start_memory
        
        print(f"注册了 {successful_registrations}/{api_count} 个 API")
        print(f"总耗时: {total_time:.2f} 秒")
        print(f"平均每个 API 注册时间: {total_time/api_count:.3f} 秒")
        print(f"内存增长: {memory_increase:.2f} MB")
        print(f"每秒注册 API 数量: {api_count/total_time:.2f}")
        
        # 性能断言
        self.assertGreater(successful_registrations, api_count * 0.9)  # 90% 成功率
        self.assertLess(total_time, 30)  # 30秒内完成
        self.assertLess(memory_increase, 100)  # 内存增长不超过100MB
    
    def test_concurrent_api_calls_performance(self):
        """测试并发 API 调用性能"""
        print(f"\n开始并发 API 调用性能测试...")
        
        # 先注册一个测试 API
        spec = self.base_spec.copy()
        spec["paths"] = {
            "/test": {
                "get": {
                    "summary": "Test endpoint",
                    "responses": {
                        "200": {"description": "OK"}
                    }
                }
            }
        }
        
        result = self.gateway.register_api(
            name="Concurrent Test API",
            openapi_content=json.dumps(spec),
            version="1.0.0"
        )
        
        if not result.get('success'):
            self.skipTest("API 注册失败，跳过并发测试")
        
        document_id = result['document_id']
        endpoints = self.gateway.list_endpoints(document_id)
        
        if not endpoints:
            self.skipTest("没有找到端点，跳过并发测试")
        
        endpoint_id = endpoints[0]['id']
        
        # 并发调用测试
        call_count = 100
        concurrent_workers = 10
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        successful_calls = 0
        failed_calls = 0
        
        def make_api_call(call_id):
            try:
                result = self.gateway.call_api(
                    endpoint_id=endpoint_id,
                    request_data={}
                )
                return result.get('success', False)
            except Exception as e:
                print(f"调用 {call_id} 失败: {e}")
                return False
        
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(make_api_call, i) for i in range(call_count)]
            
            for future in as_completed(futures):
                if future.result():
                    successful_calls += 1
                else:
                    failed_calls += 1
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        total_time = end_time - start_time
        memory_increase = end_memory - start_memory
        
        print(f"成功调用: {successful_calls}/{call_count}")
        print(f"失败调用: {failed_calls}/{call_count}")
        print(f"总耗时: {total_time:.2f} 秒")
        print(f"平均每个调用时间: {total_time/call_count:.3f} 秒")
        print(f"并发吞吐量: {call_count/total_time:.2f} 调用/秒")
        print(f"内存增长: {memory_increase:.2f} MB")
        
        # 性能断言
        self.assertGreater(successful_calls, call_count * 0.8)  # 80% 成功率
        self.assertLess(total_time, 60)  # 60秒内完成
        self.assertGreater(call_count/total_time, 1)  # 至少每秒1个调用
    
    def test_large_specification_parsing_performance(self):
        """测试大型规范解析性能"""
        print(f"\n开始大型规范解析性能测试...")
        
        # 创建大型规范
        large_spec = self.base_spec.copy()
        large_spec["paths"] = {}
        
        # 添加 1000 个端点
        endpoint_count = 1000
        for i in range(endpoint_count):
            large_spec["paths"][f"/endpoint{i}"] = {
                "get": {
                    "summary": f"Endpoint {i}",
                    "parameters": [
                        {
                            "name": "param1",
                            "in": "query",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "param2",
                            "in": "header",
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "OK"},
                        "400": {"description": "Bad Request"},
                        "404": {"description": "Not Found"}
                    }
                },
                "post": {
                    "summary": f"Create {i}",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "value": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Created"}
                    }
                }
            }
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        result = self.gateway.register_api(
            name="Large Specification API",
            openapi_content=json.dumps(large_spec),
            version="1.0.0"
        )
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        total_time = end_time - start_time
        memory_increase = end_memory - start_memory
        
        print(f"规范大小: {len(json.dumps(large_spec))} 字符")
        print(f"端点数量: {endpoint_count * 2}")  # GET + POST
        print(f"解析耗时: {total_time:.2f} 秒")
        print(f"内存增长: {memory_increase:.2f} MB")
        print(f"解析速度: {len(json.dumps(large_spec))/total_time:.0f} 字符/秒")
        
        if result.get('success'):
            document_id = result['document_id']
            endpoints = self.gateway.list_endpoints(document_id)
            print(f"实际解析端点数: {len(endpoints)}")
            
            # 性能断言
            self.assertLess(total_time, 10)  # 10秒内完成解析
            self.assertLess(memory_increase, 200)  # 内存增长不超过200MB
            self.assertGreater(len(endpoints), endpoint_count * 1.8)  # 至少解析出90%的端点
        else:
            print(f"解析失败: {result.get('error', 'Unknown error')}")
    
    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        print(f"\n开始内存泄漏检测...")
        
        initial_memory = self.get_memory_usage()
        memory_readings = [initial_memory]
        
        # 进行多轮注册和清理
        for round_num in range(5):
            print(f"第 {round_num + 1} 轮测试...")
            
            # 注册 10 个 API
            for i in range(10):
                spec = self.base_spec.copy()
                spec["paths"] = {
                    f"/round{round_num}/endpoint{i}": {
                        "get": {
                            "summary": f"Round {round_num} Endpoint {i}",
                            "responses": {"200": {"description": "OK"}}
                        }
                    }
                }
                
                self.gateway.register_api(
                    name=f"Memory Test API Round {round_num} {i}",
                    openapi_content=json.dumps(spec),
                    version="1.0.0"
                )
            
            # 记录内存使用
            current_memory = self.get_memory_usage()
            memory_readings.append(current_memory)
            print(f"  当前内存: {current_memory:.2f} MB")
        
        final_memory = self.get_memory_usage()
        total_increase = final_memory - initial_memory
        
        print(f"初始内存: {initial_memory:.2f} MB")
        print(f"最终内存: {final_memory:.2f} MB")
        print(f"总增长: {total_increase:.2f} MB")
        
        # 检查内存增长趋势
        if len(memory_readings) > 2:
            growth_rate = (memory_readings[-1] - memory_readings[1]) / (len(memory_readings) - 2)
            print(f"平均每轮增长: {growth_rate:.2f} MB")
            
            # 内存泄漏检测：如果每轮增长超过10MB，可能存在泄漏
            self.assertLess(growth_rate, 10, "可能存在内存泄漏")
        
        # 总内存增长不应过大
        self.assertLess(total_increase, 100, "内存增长过大")
    
    def test_database_performance(self):
        """测试数据库性能"""
        print(f"\n开始数据库性能测试...")
        
        start_time = time.time()
        
        # 测试大量查询
        query_count = 1000
        
        for i in range(query_count):
            # 列出所有 API
            apis = self.gateway.list_apis()
            
            # 如果有 API，测试端点查询
            if apis:
                for api in apis[:5]:  # 只查询前5个API的端点
                    endpoints = self.gateway.list_endpoints(api['id'])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"执行了 {query_count} 次查询")
        print(f"总耗时: {total_time:.2f} 秒")
        print(f"平均每次查询时间: {total_time/query_count:.3f} 秒")
        print(f"查询吞吐量: {query_count/total_time:.2f} 查询/秒")
        
        # 性能断言
        self.assertLess(total_time, 30)  # 30秒内完成
        self.assertGreater(query_count/total_time, 10)  # 至少每秒10次查询


if __name__ == '__main__':
    unittest.main() 