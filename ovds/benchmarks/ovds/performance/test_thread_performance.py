import threading
import time
import multiprocessing
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# 尝试导入resource模块（Unix系统）
try:
    import resource
except ImportError:
    resource = None


def cpu_intensive_task(iterations=1000000):
    """CPU密集型任务，用于测试线程性能"""
    result = 0
    for i in range(iterations):
        result += i * i
    return result


def test_thread_performance(num_threads, task_iterations=1000000, num_tasks=10):
    """测试指定线程数下的性能"""
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(cpu_intensive_task, task_iterations) for _ in range(num_tasks)]
        results = [future.result() for future in as_completed(futures)]
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    return {
        'num_threads': num_threads,
        'total_time': total_time,
        'avg_time_per_task': total_time / num_tasks,
        'throughput': num_tasks / total_time
    }


def find_optimal_threads(min_threads=1, max_threads=None, task_iterations=1000000, num_tasks=10, num_runs=3):
    """找到最优线程数"""
    if max_threads is None:
        # 默认测试到CPU核心数的4倍
        max_threads = multiprocessing.cpu_count() * 4
    
    cpu_count = multiprocessing.cpu_count()
    print(f"CPU核心数: {cpu_count}")
    print(f"测试线程数范围: {min_threads} - {max_threads}")
    print(f"每个测试运行 {num_runs} 次取平均值")
    print("=" * 80)
    
    results = []
    
    # 测试不同线程数
    for num_threads in range(min_threads, max_threads + 1):
        run_times = []
        
        # 多次运行取平均值
        for _ in range(num_runs):
            result = test_thread_performance(num_threads, task_iterations, num_tasks)
            run_times.append(result['total_time'])
        
        avg_time = statistics.mean(run_times)
        std_time = statistics.stdev(run_times) if len(run_times) > 1 else 0
        throughput = num_tasks / avg_time
        
        results.append({
            'num_threads': num_threads,
            'avg_time': avg_time,
            'std_time': std_time,
            'throughput': throughput
        })
        
        # 显示进度
        marker = "★" if num_threads == cpu_count else "  "
        print(f"{marker} 线程数: {num_threads:3d} | "
              f"平均时间: {avg_time:.4f}s (±{std_time:.4f}) | "
              f"吞吐量: {throughput:.2f} 任务/秒")
    
    return results


def analyze_results(results):
    """分析结果，找到最优线程数"""
    if not results:
        return None
    
    # 找到吞吐量最高的线程数
    best_throughput = max(results, key=lambda x: x['throughput'])
    
    # 找到CPU核心数对应的性能
    cpu_count = multiprocessing.cpu_count()
    cpu_result = next((r for r in results if r['num_threads'] == cpu_count), None)
    
    # 计算性能提升（相对于单线程）
    single_thread = results[0]
    improvement = (best_throughput['throughput'] / single_thread['throughput'] - 1) * 100
    
    return {
        'best_threads': best_throughput['num_threads'],
        'best_throughput': best_throughput['throughput'],
        'cpu_count': cpu_count,
        'cpu_throughput': cpu_result['throughput'] if cpu_result else None,
        'single_thread_throughput': single_thread['throughput'],
        'improvement_percent': improvement
    }


def test_max_threads():
    """测试系统能创建的最大线程数"""
    print("\n" + "=" * 80)
    print("测试系统最大线程数上限...")
    print("=" * 80)
    
    # 获取系统限制信息
    try:
        if sys.platform == 'win32':
            print("Windows系统: 线程数限制主要由内存决定")
        else:
            # Linux/Unix系统可以查看ulimit
            if resource:
                try:
                    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NPROC)
                    print(f"系统进程/线程软限制: {soft_limit if soft_limit != -1 else '无限制'}")
                    print(f"系统进程/线程硬限制: {hard_limit if hard_limit != -1 else '无限制'}")
                except:
                    pass
    except:
        pass
    
    print()
    
    # 第一阶段：快速测试，找到大致范围
    print("阶段1: 快速扫描，确定大致范围...")
    test_points = [10, 50, 100, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]
    max_successful = 0
    failed_point = None
    
    for num_threads in test_points:
        if failed_point and num_threads > failed_point:
            break
            
        try:
            success = test_thread_creation(num_threads, verbose=False)
            if success:
                max_successful = num_threads
                print(f"✓ {num_threads:6d} 个线程 - 成功")
            else:
                failed_point = num_threads
                print(f"✗ {num_threads:6d} 个线程 - 失败")
                break
        except Exception as e:
            failed_point = num_threads
            print(f"✗ {num_threads:6d} 个线程 - 异常: {str(e)[:50]}")
            break
    
    if max_successful == 0:
        print("无法创建任何线程，请检查系统配置")
        return 0
    
    # 第二阶段：二分查找，精确找到上限
    print(f"\n阶段2: 二分查找，精确确定上限 (范围: {max_successful} - {failed_point if failed_point else '未知'})...")
    
    if failed_point:
        lower_bound = max_successful
        upper_bound = failed_point
        max_threads = binary_search_max_threads(lower_bound, upper_bound)
    else:
        # 如果没有失败点，继续向上测试
        print("继续向上测试...")
        current = max_successful
        step = max_successful // 2
        
        while step >= 100:
            test_value = current + step
            try:
                if test_thread_creation(test_value, verbose=False):
                    current = test_value
                    max_successful = test_value
                    print(f"✓ {test_value:6d} 个线程 - 成功")
                else:
                    print(f"✗ {test_value:6d} 个线程 - 失败")
            except:
                print(f"✗ {test_value:6d} 个线程 - 异常")
            
            step = step // 2
        
        max_threads = max_successful
    
    # 第三阶段：验证最大线程数
    print(f"\n阶段3: 验证最大线程数 {max_threads}...")
    if test_thread_creation(max_threads, verbose=True):
        print(f"\n✓ 确认: 系统可以创建至少 {max_threads} 个线程")
    else:
        print(f"\n✗ 验证失败，实际最大线程数可能小于 {max_threads}")
        max_threads = max_successful
    
    return max_threads


def test_thread_creation(num_threads, timeout=30, verbose=True):
    """测试能否成功创建指定数量的线程"""
    threads = []
    created_count = [0]  # 使用列表以便在内部函数中修改
    error_occurred = [False]
    
    def simple_task(thread_id):
        try:
            # 简单的计算任务，确保线程真正运行
            result = 0
            for i in range(1000):
                result += i
            created_count[0] += 1
        except Exception as e:
            error_occurred[0] = True
            if verbose:
                print(f"  线程 {thread_id} 执行出错: {e}")
    
    start_time = time.perf_counter()
    
    try:
        # 创建线程
        for i in range(num_threads):
            try:
                t = threading.Thread(target=simple_task, args=(i,))
                threads.append(t)
                t.start()
            except Exception as e:
                if verbose:
                    print(f"  创建线程 {i} 时出错: {e}")
                error_occurred[0] = True
                break
        
        # 等待所有线程完成，设置超时
        join_start = time.perf_counter()
        for i, t in enumerate(threads):
            t.join(timeout=max(1, timeout - (time.perf_counter() - join_start)))
            if t.is_alive():
                if verbose:
                    print(f"  线程 {i} 超时未完成")
                error_occurred[0] = True
                break
        
        elapsed = time.perf_counter() - start_time
        
        # 检查是否所有线程都成功创建和运行
        success = (len(threads) == num_threads and 
                  created_count[0] == num_threads and 
                  not error_occurred[0] and
                  elapsed < timeout)
        
        if verbose:
            print(f"  创建线程数: {len(threads)}/{num_threads}")
            print(f"  成功执行数: {created_count[0]}/{num_threads}")
            print(f"  耗时: {elapsed:.2f}s")
        
        return success
        
    except MemoryError:
        if verbose:
            print(f"  内存不足，无法创建 {num_threads} 个线程")
        return False
    except OSError as e:
        if verbose:
            print(f"  系统资源不足: {e}")
        return False
    except Exception as e:
        if verbose:
            print(f"  未知错误: {e}")
        return False


def binary_search_max_threads(lower, upper, max_iterations=20):
    """使用二分查找找到最大线程数"""
    left, right = lower, upper
    best = lower
    iteration = 0
    
    while left <= right and iteration < max_iterations:
        iteration += 1
        mid = (left + right) // 2
        
        print(f"  测试 {mid} 个线程...", end=" ")
        
        if test_thread_creation(mid, verbose=False):
            best = mid
            left = mid + 1
            print("✓ 成功")
        else:
            right = mid - 1
            print("✗ 失败")
        
        # 如果范围很小，停止搜索
        if right - left < 10:
            break
    
    return best


def main():
    print("=" * 80)
    print("线程性能测试工具")
    print("=" * 80)
    
    # 获取系统信息
    cpu_count = multiprocessing.cpu_count()
    print(f"\n系统信息:")
    print(f"  CPU核心数: {cpu_count}")
    print(f"  操作系统: {os.name}")
    print(f"  Python版本: {multiprocessing.__file__}")
    
    # 测试最优线程数
    print("\n" + "=" * 80)
    print("阶段1: 测试最优线程数（性能测试）")
    print("=" * 80)
    
    # 根据CPU核心数调整测试范围
    max_test_threads = min(cpu_count * 8, 64)  # 最多测试到64线程或CPU核心数的8倍
    
    results = find_optimal_threads(
        min_threads=1,
        max_threads=max_test_threads,
        task_iterations=500000,  # 适中的任务量
        num_tasks=20,  # 每个线程数测试20个任务
        num_runs=3  # 每个配置运行3次取平均
    )
    
    # 分析结果
    analysis = analyze_results(results)
    
    print("\n" + "=" * 80)
    print("测试结果分析")
    print("=" * 80)
    
    if analysis:
        print(f"\n最优线程数: {analysis['best_threads']}")
        print(f"最优吞吐量: {analysis['best_throughput']:.2f} 任务/秒")
        print(f"\n单线程吞吐量: {analysis['single_thread_throughput']:.2f} 任务/秒")
        print(f"性能提升: {analysis['improvement_percent']:.1f}%")
        
        if analysis['cpu_throughput']:
            print(f"\nCPU核心数 ({analysis['cpu_count']}) 对应的吞吐量: "
                  f"{analysis['cpu_throughput']:.2f} 任务/秒")
            cpu_efficiency = (analysis['cpu_throughput'] / analysis['best_throughput']) * 100
            print(f"CPU核心数性能效率: {cpu_efficiency:.1f}% (相对于最优)")
    
    # 测试最大线程数
    print("\n" + "=" * 80)
    print("阶段2: 测试系统最大线程数（容量测试）")
    print("=" * 80)
    
    max_threads = test_max_threads()
    
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    print(f"推荐线程数（性能最优）: {analysis['best_threads'] if analysis else 'N/A'}")
    print(f"CPU核心数: {cpu_count}")
    print(f"系统最大线程数（测试）: {max_threads}")
    print(f"\n建议:")
    if analysis:
        if analysis['best_threads'] <= cpu_count:
            print(f"  - 使用 {analysis['best_threads']} 个线程（等于或接近CPU核心数）")
        else:
            print(f"  - 对于I/O密集型任务，可以使用 {analysis['best_threads']} 个线程")
            print(f"  - 对于CPU密集型任务，建议使用 {cpu_count} 个线程")
        print(f"  - 系统可以创建至少 {max_threads} 个线程（实际限制可能更高）")


def test_max_threads_only():
    """仅测试最大线程数上限"""
    print("=" * 80)
    print("系统最大线程数上限测试")
    print("=" * 80)
    
    # 获取系统信息
    cpu_count = multiprocessing.cpu_count()
    print(f"\n系统信息:")
    print(f"  CPU核心数: {cpu_count}")
    print(f"  操作系统: {os.name}")
    print(f"  平台: {sys.platform}")
    
    max_threads = test_max_threads()
    
    print("\n" + "=" * 80)
    print("最终结果")
    print("=" * 80)
    print(f"系统最大线程数上限: {max_threads}")
    print(f"\n注意:")
    print(f"  - 这是实际测试得到的值，实际限制可能受内存、系统配置等因素影响")
    print(f"  - 对于CPU密集型任务，建议使用 {cpu_count} 个线程")
    print(f"  - 对于I/O密集型任务，可以使用更多线程，但通常不需要超过 {min(max_threads, 1000)} 个")


if __name__ == "__main__":
    # 如果命令行参数包含 --max-only，只测试最大线程数
    if len(sys.argv) > 1 and '--max-only' in sys.argv:
        test_max_threads_only()
    else:
        main()

