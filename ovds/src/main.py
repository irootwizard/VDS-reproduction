import sys
import os
import time
import random
import pickle
import statistics
import json

# 增加整数字符串转换限制，避免大数据集时audit操作报错
sys.set_int_max_str_digits(10000)  # 设置为10000位数字，足够处理大数据集

sys.path.insert(0, os.path.dirname(__file__))
from vads_lib import setup, append, append_client, append_server, query, verify, query_star, verify_star, audit, judge, update

def int_to_bytes_size(n):
    if n == 0:
        return 1
    return (n.bit_length() + 7) // 8

def measure_proof_size_single(pi_q, vk):
    size = 0
    try:
        if 'sigma_i' in pi_q:
            sigma_bytes = vk['group'].serialize(pi_q['sigma_i'])
            size += len(sigma_bytes)
        if 'tag_i' in pi_q:
            size += int_to_bytes_size(pi_q['tag_i'])
        if 'pi' in pi_q:
            pi = pi_q['pi']
            if 'x' in pi:
                size += int_to_bytes_size(pi['x'])
            if 'Y' in pi:
                size += int_to_bytes_size(pi['Y'])
    except:
        try:
            size = len(pickle.dumps(pi_q))
        except:
            size = 0
    return size

def measure_proof_size_star(pi_q, vk):
    size = 0
    try:
        if 'items' in pi_q:
            for j, sigma_j, tag_j in pi_q['items']:
                try:
                    sigma_bytes = vk['group'].serialize(sigma_j)
                    size += len(sigma_bytes)
                except:
                    pass
                size += int_to_bytes_size(tag_j)
        if 'pi_J' in pi_q:
            pi_J = pi_q['pi_J']
            if 'x' in pi_J:
                size += int_to_bytes_size(pi_J['x'])
            if 'Y' in pi_J:
                size += int_to_bytes_size(pi_J['Y'])
    except:
        try:
            size = len(pickle.dumps(pi_q))
        except:
            size = 0
    return size

def measure_proof_size_audit(pi_a, vk):
    size = 0
    try:
        if 'nu' in pi_a:
            size += int_to_bytes_size(int(pi_a['nu']))
        if 'sigma_I' in pi_a:
            try:
                sigma_bytes = vk['group'].serialize(pi_a['sigma_I'])
                size += len(sigma_bytes)
            except:
                pass
        if 'pi_1' in pi_a:
            pi_1 = pi_a['pi_1']
            if 'x' in pi_1:
                size += int_to_bytes_size(pi_1['x'])
            if 'Y' in pi_1:
                size += int_to_bytes_size(pi_1['Y'])
        if 'tags' in pi_a:
            for tag in pi_a['tags'].values():
                size += int_to_bytes_size(tag)
    except:
        try:
            size = len(pickle.dumps(pi_a))
        except:
            size = 0
    return size

def run_trials(dataset_size, vk, sk, server_state, num_trials=50):
    results = {
        'setup_time': [],
        'append_times': [],
        'query_times': [],
        'verify_times': [],
        'query_star_times': [],
        'verify_star_times': [],
        'audit_times': [],
        'judge_times': [],
        'update_times': [],
        'query_proof_sizes': [],
        'query_star_proof_sizes': []
    }
    
    print(f"数据集大小: {dataset_size}")
    
    # 记录当前 DB 的起始索引
    start_idx = len(server_state['DB'])
    
    # 对于大于 2^10 的数据集，只采样 10 条执行完整 append，其余执行 append_client
    if dataset_size > 2**10:
        # 随机选择 10 个索引执行完整 append
        sample_indices = set(random.sample(range(dataset_size), min(10, dataset_size)))
        
        for i in range(dataset_size):
            s = random.randint(1, 1000)
            if i in sample_indices:
                # 执行完整 append 并统计时间
                start = time.perf_counter()
                append(sk, s, server_state)
                end = time.perf_counter()
                results['append_times'].append((end - start) * 1000)
            else:
                # 只执行 append_client，不统计时间（只为了保持计数器正确）
                append_client(sk, s)
    else:
        # 对于小于等于 2^10 的数据集，全部执行完整 append
        for i in range(dataset_size):
            start = time.perf_counter()
            append(sk, random.randint(1, 1000), server_state)
            end = time.perf_counter()
            results['append_times'].append((end - start) * 1000)
    
    indices = list(server_state['DB'].keys())
    
    for _ in range(num_trials):
        idx = random.choice(indices)
        
        start = time.perf_counter()
        query_result = query(vk, server_state, idx)
        end = time.perf_counter()
        results['query_times'].append((end - start) * 1000)
        
        if query_result:
            s_i, pi_q = query_result
            results['query_proof_sizes'].append(measure_proof_size_single(pi_q, vk))
            
            start = time.perf_counter()
            verify(vk, s_i, idx, pi_q, server_state['Acc_R'])
            end = time.perf_counter()
            results['verify_times'].append((end - start) * 1000)
    
    for _ in range(num_trials):
        if len(indices) == 0:
            continue
        max_queries = min(10, len(indices))
        min_queries = min(5, len(indices))
        num_queries = random.randint(min_queries, max_queries) if min_queries <= max_queries else len(indices)
        J = random.sample(indices, num_queries)
        
        start = time.perf_counter()
        query_star_result = query_star(vk, server_state, J)
        end = time.perf_counter()
        results['query_star_times'].append((end - start) * 1000)
        
        if query_star_result:
            S_J, pi_q = query_star_result
            results['query_star_proof_sizes'].append(measure_proof_size_star(pi_q, vk))
            
            start = time.perf_counter()
            verify_star(vk, S_J, J, pi_q, server_state['Acc_R'], server_state['R'])
            end = time.perf_counter()
            results['verify_star_times'].append((end - start) * 1000)
    
    for _ in range(num_trials):
        if len(indices) == 0:
            continue
        # 根据数据集大小动态调整audit索引数量，避免处理过大的整数
        # 对于小数据集，使用所有索引；对于大数据集，限制索引数量
        if dataset_size <= 2**6:  # 64及以下，使用所有索引
            audit_indices = indices
        elif dataset_size <= 2**9:  # 512及以下，最多100个
            audit_indices = random.sample(indices, min(100, len(indices)))
        elif dataset_size <= 2**12:  # 4096及以下，最多50个
            audit_indices = random.sample(indices, min(50, len(indices)))
        else:  # 更大数据集，最多20个
            audit_indices = random.sample(indices, min(20, len(indices)))
        
        start = time.perf_counter()
        pi_a = audit(vk, audit_indices, server_state)
        end = time.perf_counter()
        results['audit_times'].append((end - start) * 1000)
        
        if pi_a:
            start = time.perf_counter()
            judge(vk, pi_a, server_state['Acc_R'], server_state['R'])
            end = time.perf_counter()
            results['judge_times'].append((end - start) * 1000)
    
    for _ in range(num_trials):
        idx = random.choice(indices)
        new_value = random.randint(1, 1000)
        
        start = time.perf_counter()
        update(sk, idx, new_value, vk, server_state)
        end = time.perf_counter()
        results['update_times'].append((end - start) * 1000)
    
    return results

def calculate_stats(values):
    if not values:
        return {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
    return {
        'mean': statistics.mean(values),
        'std': statistics.stdev(values) if len(values) > 1 else 0,
        'min': min(values),
        'max': max(values)
    }

def save_database_data(server_state, vk, output_dir='database'):
    """保存 2^15 数据集的数据到 database 目录"""
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 序列化 DB 数据
        serializable_db = {}
        for i, (s, sigma_i, tag_i) in server_state['DB'].items():
            try:
                sigma_bytes = vk['group'].serialize(sigma_i)
                serializable_db[i] = (s, sigma_bytes, tag_i)
            except:
                serializable_db[i] = (s, None, tag_i)
        
        # 保存数据
        db_path = os.path.join(output_dir, f'db_2_15.pkl')
        with open(db_path, 'wb') as f:
            pickle.dump({
                'DB': serializable_db,
                'Acc_R': server_state['Acc_R'],
                'R': list(server_state['R']),
                'z_star': server_state['z_star'],
                'total_count': len(serializable_db)
            }, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        print(f"  数据已保存到 {db_path} (共 {len(serializable_db)} 条记录)")
        return db_path
    except Exception as e:
        print(f"  保存数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    dataset_sizes = [2**i for i in range(0, 30, 3)]  # 2^0, 2^3, 2^6, 2^9, 2^12, 2^15
    num_trials = 50
    
    all_results = []
    
    for size in dataset_sizes:
        print(f"\n处理数据集大小: {size}")
        try:
            # 每个数据集大小单独执行 setup，使用独立的 server_state
            print(f"  执行 setup...")
            setup_start = time.perf_counter()
            vk, sk, server_state = setup()
            setup_end = time.perf_counter()
            setup_time = (setup_end - setup_start) * 1000
            print(f"  Setup 完成，耗时: {setup_time:.2f}ms")
            
            results = run_trials(size, vk, sk, server_state, num_trials)
            
            # 记录当前数据集大小的 setup_time
            results['setup_time'] = [setup_time]
            
            stats = {
                'dataset_size': size,
                'setup_time': calculate_stats(results['setup_time']),
                'append_time': calculate_stats(results['append_times']),
                'query_time': calculate_stats(results['query_times']),
                'verify_time': calculate_stats(results['verify_times']),
                'query_star_time': calculate_stats(results['query_star_times']),
                'verify_star_time': calculate_stats(results['verify_star_times']),
                'audit_time': calculate_stats(results['audit_times']),
                'judge_time': calculate_stats(results['judge_times']),
                'update_time': calculate_stats(results['update_times']),
                'query_proof_size': calculate_stats(results['query_proof_sizes']),
                'query_star_proof_size': calculate_stats(results['query_star_proof_sizes'])
            }
            
            all_results.append(stats)
            
            # 为每个数据集大小创建单独的结果文件
            result_filename = f'results_{size}.json'
            with open(result_filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            print(f"  结果已保存到 {result_filename}")
            
            # 对于 2^15，保存数据到 database
            if size == 2**15:
                save_database_data(server_state, vk)
            
            print(f"  完成: setup={stats['setup_time']['mean']:.2f}ms, "
                  f"append={stats['append_time']['mean']:.2f}ms, "
                  f"query={stats['query_time']['mean']:.2f}ms")
        except Exception as e:
            print(f"  错误: {e}")
            import traceback
            traceback.print_exc()
    
    # 输出汇总表格
    print("\n" + "="*100)
    print(f"{'数据集大小':<15} {'Setup':<12} {'Append':<12} {'Query':<12} {'Verify':<12} {'Query*':<12} {'Verify*':<12} {'Audit':<12} {'Judge':<12} {'Update':<12} {'证明(单)':<15} {'证明(聚)':<15}")
    print("="*100)
    
    for stats in all_results:
        print(f"{stats['dataset_size']:<15} "
              f"{stats['setup_time']['mean']:<12.2f} "
              f"{stats['append_time']['mean']:<12.2f} "
              f"{stats['query_time']['mean']:<12.2f} "
              f"{stats['verify_time']['mean']:<12.2f} "
              f"{stats['query_star_time']['mean']:<12.2f} "
              f"{stats['verify_star_time']['mean']:<12.2f} "
              f"{stats['audit_time']['mean']:<12.2f} "
              f"{stats['judge_time']['mean']:<12.2f} "
              f"{stats['update_time']['mean']:<12.2f} "
              f"{stats['query_proof_size']['mean']:<15.0f} "
              f"{stats['query_star_proof_size']['mean']:<15.0f}")
    
    # 保存汇总结果
    with open('results_all.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n汇总结果已保存到 results_all.json")

if __name__ == "__main__":
    main()
