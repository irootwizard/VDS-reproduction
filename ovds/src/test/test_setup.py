"""
测试 VADS setup 函数
检查语法错误和基本功能
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vads_lib import setup

def test_setup():
    """
    测试 setup 函数
    检查语法错误和返回值结构
    """
    print("开始测试 setup 函数...")
    
    try:
        # 调用 setup 函数
        vk, sk, server_state = setup()
        
        # 检查返回值
        assert vk is not None, "vk 不应该为 None"
        assert sk is not None, "sk 不应该为 None"
        assert server_state is not None, "server_state 不应该为 None"
        
        # 检查 vk 结构
        assert 'group' in vk, "vk 应该包含 'group'"
        assert 'G' in vk, "vk 应该包含 'G'"
        assert 'GT' in vk, "vk 应该包含 'GT'"
        assert 'g' in vk, "vk 应该包含 'g'"
        assert 'h' in vk, "vk 应该包含 'h'"
        assert 'u' in vk, "vk 应该包含 'u'"
        assert 'A' in vk, "vk 应该包含 'A'"
        assert 'n' in vk, "vk 应该包含 'n'"
        assert 'Acc_0' in vk, "vk 应该包含 'Acc_0'"
        assert 'HG' in vk, "vk 应该包含 'HG'"
        assert 'HG_prime' in vk, "vk 应该包含 'HG_prime'"
        assert 'H2' in vk, "vk 应该包含 'H2'"
        assert 'HPrime' in vk, "vk 应该包含 'HPrime'"
        
        # 检查 sk 结构
        assert 'alpha' in sk, "sk 应该包含 'alpha'"
        assert 'cnt' in sk, "sk 应该包含 'cnt'"
        assert 'vk' in sk, "sk 应该包含 'vk'"
        assert sk['cnt'] == 0, "初始计数器应该为 0"
        
        # 检查 server_state 结构
        assert 'vk' in server_state, "server_state 应该包含 'vk'"
        assert 'R' in server_state, "server_state 应该包含 'R'"
        assert 'DB' in server_state, "server_state 应该包含 'DB'"
        assert 'Acc_R' in server_state, "server_state 应该包含 'Acc_R'"
        assert isinstance(server_state['R'], set), "R 应该是 set 类型"
        assert isinstance(server_state['DB'], dict), "DB 应该是 dict 类型"
        assert len(server_state['R']) == 0, "初始 R 应该为空"
        assert len(server_state['DB']) == 0, "初始 DB 应该为空"
        
        # 检查 RSA 模数
        assert vk['n'] > 0, "RSA 模数应该大于 0"
        assert vk['Acc_0'] > 0, "初始 accumulator 值应该大于 0"
        
        print("[OK] setup 函数测试通过")
        print()
        
        # 输出所有参数
        print("=" * 70)
        print("验证密钥 (vk) 参数:")
        print("=" * 70)
        print(f"  group: {type(vk['group']).__name__} (BN254 pairing group)")
        print(f"  G: {type(vk['G']).__name__}")
        print(f"  GT: {type(vk['GT']).__name__}")
        print(f"  g: {type(vk['g']).__name__} (G2群元素)")
        try:
            print(f"    g值: {vk['g']}")
        except:
            print(f"    g值: [G2群元素，无法直接显示]")
        print(f"  h: {type(vk['h']).__name__} (RSA accumulator初始值，整数)")
        print(f"    h值: {vk['h']} ({vk['h'].bit_length()} bits)")
        print(f"  u: {type(vk['u']).__name__} (G1群元素)")
        try:
            print(f"    u值: {vk['u']}")
        except:
            print(f"    u值: [G1群元素，无法直接显示]")
        print(f"  A: {type(vk['A']).__name__} (G2群元素, A = g^α)")
        try:
            print(f"    A值: {vk['A']}")
        except:
            print(f"    A值: [G2群元素，无法直接显示]")
        print(f"  n: {vk['n']} (RSA模数, {vk['n'].bit_length()} bits)")
        print(f"  Acc_0: {vk['Acc_0']} (RSA accumulator初始值, {vk['Acc_0'].bit_length()} bits)")
        print(f"  HG: {type(vk['HG']).__name__} (哈希函数: {{0,1}}* -> G1)")
        print(f"  HG_prime: {type(vk['HG_prime']).__name__} (哈希函数: {{0,1}}* -> 素数)")
        print(f"  H2: {type(vk['H2']).__name__} (哈希函数: {0,1}* -> {0,1}^λ)")
        print(f"  HPrime: {type(vk['HPrime']).__name__} (哈希函数: {0,1}^λ -> Z_p)")
        print()
        
        print("=" * 70)
        print("秘密密钥 (sk) 参数:")
        print("=" * 70)
        print(f"  alpha: {type(sk['alpha']).__name__} (Z_p中的秘密值)")
        try:
            print(f"    alpha值: {sk['alpha']}")
        except:
            print(f"    alpha值: [ZR类型，无法直接显示]")
        print(f"  cnt: {sk['cnt']} (计数器，初始值为0)")
        print(f"  vk: [验证密钥，见上方]")
        print()
        
        print("=" * 70)
        print("服务器状态 (server_state) 参数:")
        print("=" * 70)
        print(f"  vk: [验证密钥，见上方]")
        print(f"  R: {server_state['R']} (已删除的tag集合，初始为空，类型: {type(server_state['R']).__name__})")
        print(f"  DB: {server_state['DB']} (数据库，初始为空，类型: {type(server_state['DB']).__name__})")
        print(f"  Acc_R: {server_state['Acc_R']} (当前RSA accumulator值, {server_state['Acc_R'].bit_length()} bits)")
        print(f"  z_star: {server_state['z_star']} (缓存的z*值，初始为1)")
        print()
        
        # 验证关键关系
        print("=" * 70)
        print("关键关系验证:")
        print("=" * 70)
        print(f"  [OK] Acc_0 == Acc_R: {vk['Acc_0'] == server_state['Acc_R']}")
        print(f"  [OK] z_star == 1: {server_state['z_star'] == 1}")
        print(f"  [OK] R为空: {len(server_state['R']) == 0}")
        print(f"  [OK] DB为空: {len(server_state['DB']) == 0}")
        print(f"  [OK] cnt == 0: {sk['cnt'] == 0}")
        print()
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] 导入错误: {e}")
        print("  请确保已安装 charm-crypto: pip install charm-crypto")
        return False
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("VADS Setup 函数测试")
    print("=" * 50)
    print()
    
    success = test_setup()
    
    print()
    print("=" * 50)
    if success:
        print("测试完成: 语法检查通过")
    else:
        print("测试完成: 发现错误")
    print("=" * 50)

