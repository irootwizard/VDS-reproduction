"""
测试 VADS query 函数
按照 VADS 流程逐步生成数据并验证
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vads_lib import setup, append, query

def test_query():
    """
    测试 query 函数
    1. setup 初始化系统
    2. append 添加数据项
    3. query 查询数据项
    4. 验证返回值和证明结构
    """
    print("开始测试 query 函数...")
    
    try:
        # Step 1: 初始化系统
        print("  [1/4] 初始化系统...")
        vk, sk, server_state = setup()
        print("    ✓ 系统初始化完成")
        
        # Step 2: 添加数据项
        print("  [2/4] 添加数据项...")
        s_values = [100, 200, 300]
        for s in s_values:
            result = append(sk, s, server_state)
            assert result is not None, f"添加数据项 s={s} 失败"
        print(f"    ✓ 添加了 {len(s_values)} 个数据项")
        
        # Step 3: 查询第一个数据项
        print("  [3/4] 查询索引 0 的数据项...")
        query_result = query(vk, server_state, 0)
        
        assert query_result is not None, "query 应该返回非 None 值"
        s_i, pi_q = query_result
        
        # 验证返回值
        assert s_i == 100, "查询的数据值应该匹配"
        assert pi_q is not None, "证明不应该为 None"
        print(f"    ✓ 查询成功: s_i={s_i}")
        
        # 验证证明结构
        assert 'sigma_i' in pi_q, "证明应该包含 'sigma_i'"
        assert 'tag_i' in pi_q, "证明应该包含 'tag_i'"
        assert 'pi' in pi_q, "证明应该包含 'pi'"
        
        pi = pi_q['pi']
        assert 'x' in pi, "pi 应该包含 'x'"
        assert 'Y' in pi, "pi 应该包含 'Y'"
        print(f"    ✓ 证明结构正确: 包含 sigma_i, tag_i, pi(x, Y)")
        
        # Step 4: 查询其他数据项
        print("  [4/4] 查询其他数据项...")
        for i in range(len(s_values)):
            query_result = query(vk, server_state, i)
            assert query_result is not None, f"查询索引 {i} 失败"
            s_i, pi_q = query_result
            assert s_i == s_values[i], f"索引 {i} 的数据值应该匹配"
            print(f"    ✓ 索引 {i}: s={s_i}")
        
        # 测试查询不存在的索引
        print("    测试查询不存在的索引...")
        invalid_result = query(vk, server_state, 999)
        assert invalid_result is None, "查询不存在的索引应该返回 None"
        print("    ✓ 无效索引处理正确")
        
        print("  ✓ query 函数测试通过")
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
    print("VADS Query 函数测试")
    print("=" * 50)
    print()
    
    success = test_query()
    
    print()
    print("=" * 50)
    if success:
        print("测试完成: 通过")
    else:
        print("测试完成: 失败")
    print("=" * 50)

