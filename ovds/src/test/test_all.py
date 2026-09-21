"""
运行所有 VADS 函数测试
按照实现顺序依次测试所有函数
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test_setup import test_setup
from test_append import test_append
from test_query import test_query
from test_verify import test_verify
from test_query_star import test_query_star
from test_verify_star import test_verify_star
from test_audit import test_audit
from test_judge import test_judge

def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("VADS 完整测试套件")
    print("=" * 70)
    print()
    
    tests = [
        ("Setup", test_setup),
        ("Append", test_append),
        ("Query", test_query),
        ("Verify", test_verify),
        ("Query*", test_query_star),
        ("Verify*", test_verify_star),
        ("Audit", test_audit),
        ("Judge", test_judge),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'=' * 70}")
        print(f"测试 {name} 函数")
        print(f"{'=' * 70}")
        print()
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"  ✗ 测试 {name} 时发生异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印总结
    print()
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    print()
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {name:15s}: {status}")
    
    print()
    print(f"总计: {passed}/{total} 个测试通过")
    print("=" * 70)
    
    return all(success for _, success in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

