#!/usr/bin/env python3
"""
测试运行脚本
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print("输出:")
        print(result.stdout)
        if result.stderr:
            print("错误:")
            print(result.stderr)
        print(f"退出码: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"执行失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='运行 StepFlow Gateway 测试')
    parser.add_argument('--type', choices=['unit', 'integration', 'performance', 'all'], 
                       default='all', help='测试类型')
    parser.add_argument('--pattern', help='测试文件模式')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--clean', action='store_true', help='清理缓存后运行')
    
    args = parser.parse_args()
    
    # 设置项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 清理缓存
    if args.clean:
        print("清理缓存...")
        run_command("find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true", "清理 __pycache__")
        run_command("find . -name '*.pyc' -delete 2>/dev/null || true", "清理 .pyc 文件")
    
    # 设置 Python 路径
    python_path = f"PYTHONPATH={project_root}/src"
    
    success_count = 0
    total_count = 0
    
    if args.type in ['unit', 'all']:
        print("\n" + "="*80)
        print("运行单元测试")
        print("="*80)
        
        unit_tests = [
            ("tests/unit/test_core_base_classes.py", "核心基类测试"),
            ("tests/unit/test_registry.py", "注册表测试"),
        ]
        
        for test_file, description in unit_tests:
            if Path(test_file).exists():
                cmd = f"{python_path} python -m pytest {test_file} -v"
                if run_command(cmd, description):
                    success_count += 1
                total_count += 1
            else:
                print(f"跳过 {test_file} (文件不存在)")
    
    if args.type in ['integration', 'all']:
        print("\n" + "="*80)
        print("运行集成测试")
        print("="*80)
        
        integration_tests = [
            ("tests/integration/test_openapi_edge_cases.py", "OpenAPI 边缘情况测试"),
            ("test_openapi_plugin.py", "OpenAPI 插件测试"),
        ]
        
        for test_file, description in integration_tests:
            if Path(test_file).exists():
                cmd = f"{python_path} python {test_file}"
                if run_command(cmd, description):
                    success_count += 1
                total_count += 1
            else:
                print(f"跳过 {test_file} (文件不存在)")
    
    if args.type in ['performance', 'all']:
        print("\n" + "="*80)
        print("运行性能测试")
        print("="*80)
        
        performance_tests = [
            ("tests/integration/test_performance.py", "性能测试"),
        ]
        
        for test_file, description in performance_tests:
            if Path(test_file).exists():
                cmd = f"{python_path} python {test_file}"
                if run_command(cmd, description):
                    success_count += 1
                total_count += 1
            else:
                print(f"跳过 {test_file} (文件不存在)")
    
    # 运行特定模式的测试
    if args.pattern:
        print(f"\n运行匹配模式 '{args.pattern}' 的测试...")
        cmd = f"{python_path} python -m pytest {args.pattern} -v"
        if run_command(cmd, f"模式测试: {args.pattern}"):
            success_count += 1
        total_count += 1
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"成功: {success_count}/{total_count}")
    print(f"失败: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 