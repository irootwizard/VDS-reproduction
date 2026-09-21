"""
测试 VADS verify 函数
按照 VADS 流程逐步生成数据并验证
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vads_lib import setup, append, query, verify

def test_verify():
    """
    测试 verify 函数
    1. setup 初始化系统
    2. append 添加数据项
    3. query 查询数据项获取证明
    4. verify 验证证明
    5. 验证验证结果
    """
    print("开始测试 verify 函数...")
    
    try:
        # Step 1: 初始化系统
        print("  [1/5] 初始化系统...")
        vk, sk, server_state = setup()
        print("    ✓ 系统初始化完成")
        
        # Step 2: 添加数据项
        print("  [2/5] 添加数据项...")
        s_values = [100, 200, 300]
        for s in s_values:
            result = append(sk, s, server_state)
            assert result is not None, f"添加数据项 s={s} 失败"
        print(f"    ✓ 添加了 {len(s_values)} 个数据项")
        
        # Step 3: 查询数据项获取证明
        print("  [3/5] 查询数据项获取证明...")
        query_result = query(vk, server_state, 0)
        assert query_result is not None, "query 应该返回非 None 值"
        s_i, pi_q = query_result
        print(f"    ✓ 查询成功: s_i={s_i}")
        
        # Step 4: 验证证明
        print("  [4/5] 验证证明...")
        Acc_R = server_state['Acc_R']
        verify_result = verify(vk, s_i, 0, pi_q, Acc_R)
        
        assert verify_result is not None, "verify 应该返回非 None 值"
        assert verify_result == s_i, "验证结果应该匹配查询的数据值"
        assert verify_result == 100, "验证结果应该是 100"
        print(f"    ✓ 验证成功: 返回 s_i={verify_result}")
        
        # Step 5: 验证其他数据项
        print("  [5/5] 验证其他数据项...")
        for i in range(len(s_values)):
            query_result = query(vk, server_state, i)
            s_i, pi_q = query_result
            verify_result = verify(vk, s_i, i, pi_q, Acc_R)
            assert verify_result == s_values[i], f"索引 {i} 的验证结果应该匹配"
            print(f"    ✓ 索引 {i}: 验证通过, s={verify_result}")
        
        # 测试验证失败的情况（错误的 s_i）
        print("    测试验证失败的情况...")
        wrong_s_i = 999
        verify_result = verify(vk, wrong_s_i, 0, pi_q, Acc_R)
        assert verify_result is None, "使用错误的数据值应该验证失败"
        print("    ✓ 错误数据值验证失败（符合预期）")
        
        print("  ✓ verify 函数测试通过")
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
    print("VADS Verify 函数测试")
    print("=" * 50)
    print()
    
    success = test_verify()
    
    print()
    print("=" * 50)
    if success:
        print("测试完成: 通过")
    else:
        print("测试完成: 失败")
    print("=" * 50)

