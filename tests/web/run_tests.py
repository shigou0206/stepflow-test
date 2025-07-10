"""
Web 测试运行器
"""

import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_model_tests():
    """运行模型测试"""
    print("🧪 运行模型测试...")
    result = pytest.main([
        "tests/web/test_models.py",
        "-v",
        "--tb=short"
    ])
    return result == 0

def run_route_tests():
    """运行路由测试"""
    print("🧪 运行路由测试...")
    result = pytest.main([
        "tests/web/test_routes.py",
        "-v",
        "--tb=short"
    ])
    return result == 0

def run_all_tests():
    """运行所有 Web 测试"""
    print("🚀 开始运行 Web 测试套件...")
    
    # 运行模型测试
    model_success = run_model_tests()
    print()
    
    # 运行路由测试
    route_success = run_route_tests()
    print()
    
    # 总结
    if model_success and route_success:
        print("✅ 所有 Web 测试通过!")
        return True
    else:
        print("❌ 部分 Web 测试失败!")
        return False

def run_specific_test(test_file, test_name=None):
    """运行特定测试"""
    print(f"🧪 运行特定测试: {test_file}")
    
    cmd = [f"tests/web/{test_file}", "-v", "--tb=short"]
    if test_name:
        cmd.append(f"-k {test_name}")
    
    result = pytest.main(cmd)
    return result == 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Web 测试运行器")
    parser.add_argument("--type", choices=["models", "routes", "all"], 
                       default="all", help="测试类型")
    parser.add_argument("--file", help="特定测试文件")
    parser.add_argument("--test", help="特定测试名称")
    
    args = parser.parse_args()
    
    if args.file:
        success = run_specific_test(args.file, args.test)
    elif args.type == "models":
        success = run_model_tests()
    elif args.type == "routes":
        success = run_route_tests()
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1) 