"""
测试 VADS verify_star 函数（并发查询验证）
按照 VADS 流程逐步生成数据并验证
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vads_lib import setup, append, query_star, verify_star

def test_verify_star():
    """
    测试 verify_star 函数
    1. setup 初始化系统
    2. append 添加多个数据项
    3. query_star 并发查询获取证明
    4. verify_star 验证并发查询证明
    5. 验证验证结果
    """
    print("开始测试 verify_star 函数...")
    
    try:
        # Step 1: 初始化系统
        print("  [1/5] 初始化系统...")
        vk, sk, server_state = setup()
        print("    ✓ 系统初始化完成")
        
        # Step 2: 添加多个数据项
        print("  [2/5] 添加多个数据项...")
        s_values = [100, 200, 300, 400, 500]
        for s in s_values:
            result = append(sk, s, server_state)
            assert result is not None, f"添加数据项 s={s} 失败"
        print(f"    ✓ 添加了 {len(s_values)} 个数据项")
        
        # Step 3: 并发查询获取证明
        print("  [3/5] 并发查询获取证明...")
        J = [0, 2, 4]  # 查询索引 0, 2, 4
        query_result = query_star(vk, server_state, J)
        assert query_result is not None, "query_star 应该返回非 None 值"
        S_J, pi_q = query_result
        print(f"    ✓ 查询成功: J={J}, S_J={S_J}")
        
        # Step 4: 验证并发查询证明
        print("  [4/5] 验证并发查询证明...")
        Acc_R = server_state['Acc_R']
        R = server_state['R']
        verify_result = verify_star(vk, S_J, J, pi_q, Acc_R, R)
        
        assert verify_result is not None, "verify_star 应该返回非 None 值"
        assert verify_result == S_J, "验证结果应该匹配查询的数据值列表"
        assert verify_result == [s_values[i] for i in J], "验证结果应该匹配"
        print(f"    ✓ 验证成功: 返回 S_J={verify_result}")
        
        # Step 5: 测试不同的查询组合
        print("  [5/5] 测试不同的查询组合...")
        test_cases = [
            [0],  # 单个查询
            [0, 1],  # 两个查询
            [1, 2, 3],  # 三个查询
            [0, 1, 2, 3, 4],  # 全部查询
        ]
        
        for J_test in test_cases:
            query_result = query_star(vk, server_state, J_test)
            S_J_test, pi_q_test = query_result
            verify_result = verify_star(vk, S_J_test, J_test, pi_q_test, Acc_R, R)
            assert verify_result == [s_values[i] for i in J_test], f"J={J_test} 的验证结果应该匹配"
            print(f"    ✓ J={J_test}: 验证通过, S_J={verify_result}")
        
        # 测试验证失败的情况（错误的 S_J）
        print("    测试验证失败的情况...")
        wrong_S_J = [999, 888, 777]
        verify_result = verify_star(vk, wrong_S_J, J, pi_q, Acc_R, R)
        assert verify_result is None, "使用错误的数据值列表应该验证失败"
        print("    ✓ 错误数据值列表验证失败（符合预期）")
        
        print("  ✓ verify_star 函数测试通过")
        return True
        
    except ImportError as e:
        print(f"  ✗ 导入错误: {e}")
        print("    请确保已安装 charm-crypto: pip install charm-crypto")
        return False
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("VADS Verify* 函数测试（并发查询验证）")
    print("=" * 50)
    print()
    
    success = test_verify_star()
    
    print()
    print("=" * 50)
    if success:
        print("测试完成: 通过")
    else:
        print("测试完成: 失败")
    print("=" * 50)









