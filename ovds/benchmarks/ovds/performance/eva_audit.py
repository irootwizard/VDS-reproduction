import sys
import os
import time
import random
import statistics
import json

# 增加整数字符串转换限制，避免大数据集时audit操作报错
# 设置为更大的值以处理大审计集（200-1000条数据）时的大整数转换
sys.set_int_max_str_digits(100000)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))
from vads_lib import setup, append, audit, judge

def calculate_stats(values):
    """计算统计信息"""
    if not values:
        return {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
    return {
        'mean': statistics.mean(values),
        'std': statistics.stdev(values) if len(values) > 1 else 0,
        'min': min(values),
        'max': max(values)
    }

def main():
    """评估 audit 和 judge 关于审计集大小的时间开销变化"""
    # 固定数据集大小为 2^10
    dataset_size = 2**10  # 1024
    
    # 审计集大小：200, 400, 600, 800, 1000
    audit_sizes = [200, 400, 600, 800, 1000]
    
    # 每个审计集大小运行 50 次
    num_trials = 50
    
    print(f"数据集大小: {dataset_size}")
    print(f"审计集大小: {audit_sizes}")
    print(f"每个审计集大小运行次数: {num_trials}")
    print("="*80)
    
    # Step 1: 初始化系统
    print(f"\n[1/3] 初始化系统...")
    setup_start = time.perf_counter()
    vk, sk, server_state = setup()
    setup_end = time.perf_counter()
    setup_time = (setup_end - setup_start) * 1000
    print(f"  Setup 完成，耗时: {setup_time:.2f}ms")
    
    # Step 2: 添加 2^10 条数据
    print(f"\n[2/3] 添加 {dataset_size} 条数据...")
    append_start = time.perf_counter()
    for i in range(dataset_size):
        s = random.randint(1, 1000)
        append(sk, s, server_state)
        if (i + 1) % 100 == 0:
            print(f"  已添加 {i + 1}/{dataset_size} 条数据...")
    append_end = time.perf_counter()
    append_time = (append_end - append_start) * 1000
    print(f"  添加数据完成，耗时: {append_time:.2f}ms")
    
    # 获取所有可用索引
    indices = list(server_state['DB'].keys())
    print(f"  可用索引数量: {len(indices)}")
    
    # Step 3: 对每个审计集大小进行评估
    print(f"\n[3/3] 评估不同审计集大小的时间开销...")
    all_results = []
    
    for audit_size in audit_sizes:
        print(f"\n  处理审计集大小: {audit_size}")
        
        # 检查审计集大小是否超过可用索引数量
        if audit_size > len(indices):
            print(f"    警告: 审计集大小 {audit_size} 超过可用索引数量 {len(indices)}，跳过")
            continue
        
        audit_times = []
        judge_times = []
        
        for trial in range(num_trials):
            # 随机选择 audit_size 个索引
            audit_indices = random.sample(indices, audit_size)
            
            # 执行 audit 并记录时间
            start = time.perf_counter()
            pi_a = audit(vk, audit_indices, server_state)
            end = time.perf_counter()
            audit_time = (end - start) * 1000
            audit_times.append(audit_time)
            
            # 如果 audit 成功，执行 judge 并记录时间
            if pi_a:
                start = time.perf_counter()
                judge_result = judge(vk, pi_a, server_state['Acc_R'], server_state['R'])
                end = time.perf_counter()
                judge_time = (end - start) * 1000
                judge_times.append(judge_time)
                
                # 验证 judge 结果应该为 1
                if judge_result != 1:
                    print(f"    警告: 第 {trial + 1} 次试验 judge 验证失败")
            else:
                print(f"    警告: 第 {trial + 1} 次试验 audit 返回 None")
            
            # 显示进度
            if (trial + 1) % 10 == 0:
                print(f"    进度: {trial + 1}/{num_trials}")
        
        # 计算统计信息
        audit_stats = calculate_stats(audit_times)
        judge_stats = calculate_stats(judge_times)
        
        result = {
            'audit_size': audit_size,
            'audit_time': audit_stats,
            'judge_time': judge_stats,
            'audit_times': audit_times,  # 保存所有原始数据
            'judge_times': judge_times   # 保存所有原始数据
        }
        
        all_results.append(result)
        
        print(f"    Audit 平均时间: {audit_stats['mean']:.2f}ms (std: {audit_stats['std']:.2f}ms)")
        print(f"    Judge 平均时间: {judge_stats['mean']:.2f}ms (std: {judge_stats['std']:.2f}ms)")
    
    # 保存结果
    output_filename = os.path.join(PROJECT_ROOT, 'results', 'ovds', 'raw', 'eva_audit_results.json')
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'dataset_size': dataset_size,
            'setup_time': setup_time,
            'append_time': append_time,
            'results': all_results
        }, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存到 {output_filename}")
    
    # 输出汇总表格
    print("\n" + "="*80)
    print(f"{'审计集大小':<15} {'Audit 平均时间(ms)':<20} {'Audit 标准差(ms)':<20} {'Judge 平均时间(ms)':<20} {'Judge 标准差(ms)':<20}")
    print("="*80)
    
    for result in all_results:
        audit_stats = result['audit_time']
        judge_stats = result['judge_time']
        print(f"{result['audit_size']:<15} "
              f"{audit_stats['mean']:<20.2f} "
              f"{audit_stats['std']:<20.2f} "
              f"{judge_stats['mean']:<20.2f} "
              f"{judge_stats['std']:<20.2f}")
    
    print("\n评估完成！")

if __name__ == "__main__":
    main()

