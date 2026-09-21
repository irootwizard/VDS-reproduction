"""
测量单个数据项的大小
"""

import sys
import os

# 添加父目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from vads_lib import setup, append

def int_to_bytes_size(n):
    """计算整数实际需要的字节数"""
    if n == 0:
        return 1
    return (n.bit_length() + 7) // 8

def measure_item_size():
    """测量单个数据项的大小"""
    print("初始化系统...")
    vk, sk, server_state = setup()
    
    print("添加一个数据项...")
    result = append(sk, 100, server_state)
    assert result is not None, "添加数据项失败"
    
    i, s, sigma_i, tag_i = result
    
    # 获取数据项（注意：现在数据项不包含索引 i，索引 i 作为字典 key）
    item = server_state['DB'][i]
    s_stored, sigma_i_stored, tag_i_stored = item
    
    print("\n数据项组件实际大小（字节表示）:")
    # 计算整数实际需要的字节数
    i_bytes = int_to_bytes_size(i)
    s_bytes = int_to_bytes_size(s)
    tag_bytes = int_to_bytes_size(tag_i)
    
    print(f"  索引 i (字典key): {i_bytes} 字节 (值={i}, {i.bit_length()} bits) [不存储在元组中]")
    print(f"  数据值 s: {s_bytes} 字节 (值={s}, {s.bit_length()} bits)")
    print(f"  tag_i: {tag_bytes} 字节 (值={tag_i}, {tag_i.bit_length()} bits)")
    
    # 测量 BLS 签名大小
    sigma_bytes = None
    sigma_obj_size = sys.getsizeof(sigma_i)
    try:
        sigma_bytes = vk['group'].serialize(sigma_i)
        print(f"  BLS签名 sigma_i: {len(sigma_bytes)} 字节 (序列化)")
        print(f"  BLS签名 sigma_i: {sigma_obj_size} 字节 (Python对象大小)")
    except Exception as e:
        print(f"  BLS签名 sigma_i: 无法序列化 ({e})")
        print(f"  BLS签名 sigma_i: {sigma_obj_size} 字节 (Python对象大小)")
    
    # 计算实际存储大小（数据项元组，不包括索引 i）
    print(f"\n实际存储大小（数据项元组，索引 i 作为字典 key）:")
    print(f"  - 数据值 s: {s_bytes} 字节")
    print(f"  - tag_i: {tag_bytes} 字节")
    if sigma_bytes:
        print(f"  - BLS签名: {len(sigma_bytes)} 字节")
        total_bytes = s_bytes + tag_bytes + len(sigma_bytes)
    else:
        print(f"  - BLS签名: 未知（无法序列化）")
        total_bytes = s_bytes + tag_bytes
    
    print(f"  = 数据项元组总计: {total_bytes} 字节")
    print(f"  (索引 i 作为字典 key，额外开销: {i_bytes} 字节)")
    
    # Python对象开销（仅供参考）
    print(f"\nPython对象开销（仅供参考）:")
    print(f"  sys.getsizeof(索引): {sys.getsizeof(i)} 字节")
    print(f"  sys.getsizeof(数据值): {sys.getsizeof(s)} 字节")
    print(f"  sys.getsizeof(tag): {sys.getsizeof(tag_i)} 字节")
    print(f"  sys.getsizeof(BLS签名对象): {sigma_obj_size} 字节")
    print(f"  sys.getsizeof(元组): {sys.getsizeof(item)} 字节")
    
    # 尝试创建可序列化版本
    print(f"\n可序列化版本大小:")
    try:
        import pickle
        # 创建可序列化的数据项（用字节表示，不包含索引 i）
        serializable_item = (s, tag_i, sigma_bytes if sigma_bytes else b'')
        pickled = pickle.dumps(serializable_item)
        print(f"  序列化后（不含索引）: {len(pickled)} 字节")
        # 如果包含索引（作为字典 key 的序列化）
        serializable_with_key = {i: serializable_item}
        pickled_with_key = pickle.dumps(serializable_with_key)
        print(f"  序列化后（含字典key）: {len(pickled_with_key)} 字节")
    except Exception as e:
        print(f"  无法序列化: {e}")

if __name__ == "__main__":
    try:
        measure_item_size()
    except ImportError as e:
        print(f"错误: {e}")
        print("请确保已安装 charm-crypto: pip install charm-crypto")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

