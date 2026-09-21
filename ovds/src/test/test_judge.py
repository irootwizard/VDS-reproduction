"""
测试 VADS judge 函数
按照 VADS 流程逐步生成数据并验证
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vads_lib import setup, append, audit, judge

def test_judge():
    """
    测试 judge 函数
    1. setup 初始化系统
    2. append 添加多个数据项
    3. audit 进行审计获取证明
    4. judge 验证审计证明
    5. 验证验证结果
    """
    print("开始测试 judge 函数...")
    
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
        
        # Step 3: 审计所有数据
        print("  [3/5] 审计所有数据...")
        pi_a = audit(vk, None, server_state)
        assert pi_a is not None, "audit 应该返回非 None 值"
        print(f"    ✓ 审计成功: I={pi_a['I']}")
        
        # Step 4: 验证审计证明
        print("  [4/5] 验证审计证明...")
        Acc_R = server_state['Acc_R']
        R = server_state['R']
        judge_result = judge(vk, pi_a, Acc_R, R)
        
        assert judge_result == 1, "judge 应该返回 1（验证通过）"
        print(f"    ✓ 验证成功: 返回 {judge_result}")
        
        # Step 5: 测试不同的审计组合
        print("  [5/5] 测试不同的审计组合...")
        test_cases = [
            [0],  # 单个数据项
            [0, 1],  # 两个数据项
            [0, 2, 4],  # 三个数据项
            [0, 1, 2, 3, 4],  # 全部数据项
        ]
        
        for I_test in test_cases:
            pi_a_test = audit(vk, I_test, server_state)
            assert pi_a_test is not None, f"审计 I={I_test} 失败"
            judge_result = judge(vk, pi_a_test, Acc_R, R)
            assert judge_result == 1, f"验证 I={I_test} 应该通过"
            print(f"    ✓ I={I_test}: 验证通过")
        
        # 测试验证失败的情况（错误的证明结构）
        print("    测试验证失败的情况...")
        wrong_pi_a = {'nu': pi_a['nu'], 'sigma_I': pi_a['sigma_I']}  # 缺少必要字段
        judge_result = judge(vk, wrong_pi_a, Acc_R, R)
        assert judge_result == 0, "错误的证明结构应该验证失败"
        print("    ✓ 错误证明结构验证失败（符合预期）")
        
        print("  ✓ judge 函数测试通过")
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
    print("VADS Judge 函数测试")
    print("=" * 50)
    print()
    
    success = test_judge()
    
    print()
    print("=" * 50)
    if success:
        print("测试完成: 通过")
    else:
        print("测试完成: 失败")
    print("=" * 50)









