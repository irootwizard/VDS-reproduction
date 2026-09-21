"""
测试 VADS query_star 函数（并发查询）
按照 VADS 流程逐步生成数据并验证
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vads_lib import setup, append, query_star

def test_query_star():
    """
    测试 query_star 函数
    1. setup 初始化系统
    2. append 添加多个数据项
    3. query_star 并发查询多个数据项
    4. 验证返回值和证明结构
    """
    print("开始测试 query_star 函数...")
    
    try:
        # Step 1: 初始化系统
        print("  [1/4] 初始化系统...")
        vk, sk, server_state = setup()
        print("    ✓ 系统初始化完成")
        
        # Step 2: 添加多个数据项
        print("  [2/4] 添加多个数据项...")
        s_values = [100, 200, 300, 400, 500]
        for s in s_values:
            result = append(sk, s, server_state)
            assert result is not None, f"添加数据项 s={s} 失败"
        print(f"    ✓ 添加了 {len(s_values)} 个数据项")
        
        # Step 3: 并发查询多个数据项
        print("  [3/4] 并发查询多个数据项...")
        J = [0, 2, 4]  # 查询索引 0, 2, 4
        query_result = query_star(vk, server_state, J)
        
        assert query_result is not None, "query_star 应该返回非 None 值"
        S_J, pi_q = query_result
        
        # 验证返回值
        assert len(S_J) == len(J), "返回的数据值列表长度应该匹配"
        assert S_J == [s_values[i] for i in J], "返回的数据值应该匹配"
        print(f"    ✓ 查询成功: J={J}, S_J={S_J}")
        
        # 验证证明结构
        assert 'items' in pi_q, "证明应该包含 'items'"
        assert 'pi_J' in pi_q, "证明应该包含 'pi_J'"
        
        items = pi_q['items']
        assert len(items) == len(J), "items 长度应该匹配"
        for idx, (j, sigma_j, tag_j) in enumerate(items):
            assert j == J[idx], f"items 中的索引应该匹配"
            assert sigma_j is not None, "签名不应该为 None"
            assert tag_j is not None, "tag 不应该为 None"
        print(f"    ✓ 证明结构正确: items数量={len(items)}")
        
        pi_J = pi_q['pi_J']
        assert 'V' in pi_J, "pi_J 应该包含 'V'"
        assert 'Y' in pi_J, "pi_J 应该包含 'Y'"
        assert 'T_1' in pi_J, "pi_J 应该包含 'T_1'"
        assert 'T_2' in pi_J, "pi_J 应该包含 'T_2'"
        assert 'X_prime' in pi_J, "pi_J 应该包含 'X_prime'"
        assert 'r' in pi_J, "pi_J 应该包含 'r'"
        print(f"    ✓ 聚合证明结构正确: 包含 V, Y, T_1, T_2, X', r")
        
        # Step 4: 测试不同的查询组合
        print("  [4/4] 测试不同的查询组合...")
        test_cases = [
            [0],  # 单个查询
            [0, 1],  # 两个查询
            [1, 2, 3],  # 三个查询
            [0, 1, 2, 3, 4],  # 全部查询
        ]
        
        for J_test in test_cases:
            query_result = query_star(vk, server_state, J_test)
            assert query_result is not None, f"查询 J={J_test} 失败"
            S_J_test, pi_q_test = query_result
            assert len(S_J_test) == len(J_test), "返回的数据值列表长度应该匹配"
            assert S_J_test == [s_values[i] for i in J_test], "返回的数据值应该匹配"
            print(f"    ✓ J={J_test}: 查询成功, S_J={S_J_test}")
        
        # 测试查询不存在的索引
        print("    测试查询不存在的索引...")
        invalid_result = query_star(vk, server_state, [0, 999])
        assert invalid_result is None, "查询包含不存在索引的集合应该返回 None"
        print("    ✓ 无效索引处理正确")
        
        print("  ✓ query_star 函数测试通过")
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
    print("VADS Query* 函数测试（并发查询）")
    print("=" * 50)
    print()
    
    success = test_query_star()
    
    print()
    print("=" * 50)
    if success:
        print("测试完成: 通过")
    else:
        print("测试完成: 失败")
    print("=" * 50)









