"""
测试 VADS audit 函数
按照 VADS 流程逐步生成数据并验证
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vads_lib import setup, append, audit

def test_audit():
    """
    测试 audit 函数
    1. setup 初始化系统
    2. append 添加多个数据项
    3. audit 进行审计
    4. 验证返回值和证明结构
    """
    print("开始测试 audit 函数...")
    
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
        
        # Step 3: 审计所有数据
        print("  [3/4] 审计所有数据...")
        pi_a = audit(vk, None, server_state)
        
        assert pi_a is not None, "audit 应该返回非 None 值"
        
        # 验证证明结构
        assert 'nu' in pi_a, "证明应该包含 'nu'"
        assert 'sigma_I' in pi_a, "证明应该包含 'sigma_I'"
        assert 'pi_1' in pi_a, "证明应该包含 'pi_1'"
        assert 'tags' in pi_a, "证明应该包含 'tags'"
        assert 'v_dict' in pi_a, "证明应该包含 'v_dict'"
        assert 'I' in pi_a, "证明应该包含 'I'"
        print(f"    ✓ 审计成功: I={pi_a['I']}")
        
        # 验证证明内容
        assert len(pi_a['I']) == len(s_values), "审计索引数量应该匹配"
        assert len(pi_a['tags']) == len(s_values), "tags 数量应该匹配"
        assert len(pi_a['v_dict']) == len(s_values), "v_dict 数量应该匹配"
        print(f"    ✓ 证明结构正确: nu存在, sigma_I存在, pi_1存在")
        
        # Step 4: 审计部分数据
        print("  [4/4] 审计部分数据...")
        I_partial = [0, 2, 4]
        pi_a_partial = audit(vk, I_partial, server_state)
        
        assert pi_a_partial is not None, "部分审计应该返回非 None 值"
        assert pi_a_partial['I'] == I_partial, "审计索引应该匹配"
        assert len(pi_a_partial['tags']) == len(I_partial), "tags 数量应该匹配"
        print(f"    ✓ 部分审计成功: I={I_partial}")
        
        # 测试空数据库
        print("    测试空数据库...")
        vk_empty, sk_empty, server_state_empty = setup()
        pi_a_empty = audit(vk_empty, None, server_state_empty)
        assert pi_a_empty is None, "空数据库应该返回 None"
        print("    ✓ 空数据库处理正确")
        
        print("  ✓ audit 函数测试通过")
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
    print("VADS Audit 函数测试")
    print("=" * 50)
    print()
    
    success = test_audit()
    
    print()
    print("=" * 50)
    if success:
        print("测试完成: 通过")
    else:
        print("测试完成: 失败")
    print("=" * 50)









