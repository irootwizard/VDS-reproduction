"""
测试 VADS append 函数
按照 VADS 流程逐步生成数据并验证
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vads_lib import setup, append

def test_append():
    """
    测试 append 函数
    1. 先调用 setup 初始化系统
    2. 调用 append 添加数据项
    3. 验证返回值和数据库状态
    """
    print("开始测试 append 函数...")
    
    try:
        # Step 1: 初始化系统
        print("  [1/3] 初始化系统...")
        vk, sk, server_state = setup()
        initial_cnt = sk['cnt']
        initial_db_size = len(server_state['DB'])
        
        assert initial_cnt == 0, "初始计数器应该为 0"
        assert initial_db_size == 0, "初始数据库应该为空"
        print(f"    ✓ 初始状态: cnt={initial_cnt}, DB大小={initial_db_size}")
        
        # Step 2: 添加第一个数据项
        print("  [2/3] 添加数据项 s=100...")
        s1 = 100
        result1 = append(sk, s1, server_state)
        
        assert result1 is not None, "append 应该返回非 None 值"
        i1, s1_returned, sigma_i1, tag_i1 = result1
        
        # 验证返回值
        assert i1 == 0, "第一个数据项的索引应该是 0"
        assert s1_returned == s1, "返回的数据值应该匹配"
        assert sigma_i1 is not None, "签名不应该为 None"
        assert tag_i1 is not None, "tag 不应该为 None"
        print(f"    ✓ 添加成功: i={i1}, s={s1_returned}, tag={tag_i1}")
        
        # 验证数据库状态
        assert sk['cnt'] == 1, "计数器应该增加到 1"
        assert len(server_state['DB']) == 1, "数据库应该包含 1 个条目"
        assert 0 in server_state['DB'], "数据库应该包含索引 0"
        
        db_entry = server_state['DB'][0]
        assert db_entry == (i1, s1_returned, sigma_i1, tag_i1), "数据库条目应该匹配"
        print(f"    ✓ 数据库状态: cnt={sk['cnt']}, DB大小={len(server_state['DB'])}")
        
        # Step 3: 添加第二个数据项
        print("  [3/3] 添加第二个数据项 s=200...")
        s2 = 200
        result2 = append(sk, s2, server_state)
        
        assert result2 is not None, "append 应该返回非 None 值"
        i2, s2_returned, sigma_i2, tag_i2 = result2
        
        assert i2 == 1, "第二个数据项的索引应该是 1"
        assert s2_returned == s2, "返回的数据值应该匹配"
        assert tag_i1 != tag_i2, "不同的数据项应该有不同的 tag"
        print(f"    ✓ 添加成功: i={i2}, s={s2_returned}, tag={tag_i2}")
        
        # 验证最终状态
        assert sk['cnt'] == 2, "计数器应该增加到 2"
        assert len(server_state['DB']) == 2, "数据库应该包含 2 个条目"
        assert 0 in server_state['DB'] and 1 in server_state['DB'], "数据库应该包含两个索引"
        print(f"    ✓ 最终状态: cnt={sk['cnt']}, DB大小={len(server_state['DB'])}")
        
        print("  ✓ append 函数测试通过")
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
    print("VADS Append 函数测试")
    print("=" * 50)
    print()
    
    success = test_append()
    
    print()
    print("=" * 50)
    if success:
        print("测试完成: 通过")
    else:
        print("测试完成: 失败")
    print("=" * 50)
