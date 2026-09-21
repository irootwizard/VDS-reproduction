"""
计算 2^30 次 append 的存储开销
基于 eva_data_size.py 的测量结果
"""

import sys
import os

# 添加父目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

def int_to_bytes_size(n):
    """计算整数实际需要的字节数"""
    if n == 0:
        return 1
    return (n.bit_length() + 7) // 8

def calculate_storage_cost():
    """
    计算 2^30 次 append 的存储开销
    基于单个数据项的测量结果
    """
    # 基于 eva_data_size.py 的实际测量结果:
    # - 数据值 s: 1 字节（值=100时），但考虑到可能的值范围，平均估计 2-4 字节
    # - tag_i: 16 字节（128 bits，实际测量值）
    # - BLS签名 sigma_i: 46 字节（序列化，实际测量值）
    # - 序列化后（含字典key）: 89 字节（实际测量值）
    
    # 基于实际测量值的估计
    s_bytes_avg = 2  # 数据值平均大小（实际测量1字节，但考虑范围，保守估计2字节）
    tag_bytes = 16   # tag_i: 128 bits = 16 字节（实际测量值）
    sigma_bytes = 46 # BLS签名: 46 字节（实际测量值，序列化）
    
    # 单个数据项大小（元组内容，不包括索引）
    item_tuple_bytes = s_bytes_avg + tag_bytes + sigma_bytes  # 2 + 16 + 46 = 64 字节
    
    # 对于mmap持久化，使用序列化后的实际大小（更准确）
    # 实际测量：序列化后（含字典key）: 89 字节
    # 但考虑到索引会增长（2^30需要4字节），使用更保守的估计
    serialized_item_bytes = 89  # 实际测量值（含字典key的序列化大小）
    
    # 索引 i 的大小（作为字典key）
    # 2^30 的索引需要 log2(2^30) = 30 bits，约 4 字节
    index_bytes = 4
    
    # 对于mmap存储，使用固定大小的记录格式，避免Python字典开销
    # 每条记录：索引(4字节) + 数据值(4字节，固定) + tag(16字节) + 签名(46字节) = 70字节
    # 加上对齐和元数据，每条记录约 72 字节
    mmap_record_size = 72  # 固定大小记录，便于mmap访问
    
    # Python字典开销（内存中，如果使用字典）
    # 字典条目开销：hash值(8字节) + key指针(8字节) + value指针(8字节) + 其他开销
    dict_entry_overhead = 32  # 保守估计
    
    # 单个数据项总开销（内存中，使用字典）
    item_total_bytes_memory = item_tuple_bytes + index_bytes + dict_entry_overhead
    
    # 单个数据项总开销（mmap持久化，固定大小记录）
    item_total_bytes_mmap = mmap_record_size
    
    # 2^30 次 append
    num_items = 2**30
    
    # 数据项总大小（内存中，使用字典）
    db_total_bytes_memory = item_total_bytes_memory * num_items
    
    # 数据项总大小（mmap持久化，固定大小记录）
    db_total_bytes_mmap = item_total_bytes_mmap * num_items
    
    # 其他开销
    # 1. server_state 其他字段
    #    - Acc_R: RSA accumulator值，3072 bits = 384 字节
    #    - z_star: 整数，约 384 字节
    #    - R: set()，假设删除操作不多，忽略
    acc_r_bytes = 384
    z_star_bytes = 384
    server_state_overhead = acc_r_bytes + z_star_bytes
    
    # 2. vk (验证密钥) - 通常只存储一次，不算在append开销中
    #    但需要持久化，约几KB，可忽略
    
    # 3. 文件系统开销（mmap文件头、索引等）
    #    - mmap文件头: 约 1KB（包含元数据、记录数量等）
    #    - 对于固定大小记录，不需要额外索引文件（直接通过偏移量访问）
    filesystem_overhead = 1024  # 1KB（文件头）
    
    # mmap文件总大小（固定大小记录，便于随机访问）
    mmap_file_size = db_total_bytes_mmap + filesystem_overhead
    
    # 内存中总开销（如果全部加载到内存）
    total_bytes_memory = db_total_bytes_memory + server_state_overhead
    
    # mmap持久化总开销（磁盘空间）
    total_bytes_mmap = mmap_file_size + server_state_overhead
    
    # 转换为更易读的单位
    total_gb_memory = total_bytes_memory / (1024**3)
    total_tb_memory = total_bytes_memory / (1024**4)
    total_gb_mmap = total_bytes_mmap / (1024**3)
    total_tb_mmap = total_bytes_mmap / (1024**4)
    
    print("=" * 80)
    print("2^30 次 append 存储开销计算（基于实际测量值）")
    print("=" * 80)
    print(f"\n单个数据项开销（基于实际测量）:")
    print(f"  - 数据值 s: {s_bytes_avg} 字节（实际测量1字节，保守估计2字节）")
    print(f"  - tag_i: {tag_bytes} 字节 (128 bits，实际测量值)")
    print(f"  - BLS签名 sigma_i: {sigma_bytes} 字节（实际测量值，序列化）")
    print(f"  - 元组内容总计: {item_tuple_bytes} 字节")
    print(f"  - 序列化后（含字典key）: {serialized_item_bytes} 字节（实际测量值）")
    
    print(f"\n存储方案对比:")
    print(f"  内存存储（Python字典）:")
    print(f"    - 索引 i (字典key): {index_bytes} 字节")
    print(f"    - 字典条目开销: {dict_entry_overhead} 字节")
    print(f"    - 单个数据项总计: {item_total_bytes_memory} 字节")
    print(f"  mmap持久化（固定大小记录）:")
    print(f"    - 每条记录: {mmap_record_size} 字节（索引4 + 数据4 + tag16 + 签名46 + 对齐2）")
    print(f"    - 优点: 固定大小，便于随机访问，无需额外索引")
    
    print(f"\n2^30 次 append 开销:")
    print(f"  - 数据项总数: {num_items:,} ({num_items / (1024**3):.2f} 十亿)")
    print(f"  - 内存存储（字典）: {db_total_bytes_memory / (1024**3):.2f} GB")
    print(f"  - mmap持久化（固定记录）: {db_total_bytes_mmap / (1024**3):.2f} GB")
    
    print(f"\n其他开销:")
    print(f"  - Acc_R: {acc_r_bytes} 字节")
    print(f"  - z_star: {z_star_bytes} 字节")
    print(f"  - mmap文件头: {filesystem_overhead / 1024:.2f} KB")
    
    print(f"\n总开销:")
    print(f"  内存存储（如果全部加载）:")
    print(f"    - 总计: {total_bytes_memory:,} 字节")
    print(f"    - 总计: {total_gb_memory:.2f} GB")
    print(f"    - 总计: {total_tb_memory:.4f} TB")
    print(f"  mmap持久化（磁盘空间）:")
    print(f"    - 总计: {total_bytes_mmap:,} 字节")
    print(f"    - 总计: {total_gb_mmap:.2f} GB")
    print(f"    - 总计: {total_tb_mmap:.4f} TB")
    
    print(f"\n内存限制分析 (8GB = {8 * 1024**3:,} 字节):")
    memory_limit = 8 * 1024**3
    if total_bytes_memory > memory_limit:
        print(f"  ⚠ 内存存储 ({total_gb_memory:.2f} GB) 超过内存限制 (8 GB)")
        print(f"  ⚠ 必须使用 mmap 进行持久化和内存映射")
        print(f"  ✓ mmap方案: 磁盘空间 {total_gb_mmap:.2f} GB，内存按需加载")
        print(f"  ✓ mmap优势: 固定大小记录，O(1)随机访问，无需全部加载到内存")
    else:
        print(f"  ✓ 内存存储 ({total_gb_memory:.2f} GB) 在内存限制内 (8 GB)")
        print(f"  ℹ 但使用mmap仍可减少内存占用，提高性能")
    
    return {
        'item_tuple_bytes': item_tuple_bytes,
        'item_total_bytes_memory': item_total_bytes_memory,
        'item_total_bytes_mmap': item_total_bytes_mmap,
        'mmap_record_size': mmap_record_size,
        'num_items': num_items,
        'db_total_bytes_memory': db_total_bytes_memory,
        'db_total_bytes_mmap': db_total_bytes_mmap,
        'total_bytes_memory': total_bytes_memory,
        'total_bytes_mmap': total_bytes_mmap,
        'total_gb_memory': total_gb_memory,
        'total_gb_mmap': total_gb_mmap
    }

if __name__ == "__main__":
    try:
        calculate_storage_cost()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
