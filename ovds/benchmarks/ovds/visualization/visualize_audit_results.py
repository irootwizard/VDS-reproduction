"""
根据 eva_audit_results.json 生成可视化图表
显示审计和判断时间随审计挑战集大小的变化
"""
import json
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建基于时间的输出文件夹（在根目录的 generated 文件夹下）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
generated_dir = os.path.join(PROJECT_ROOT, 'results', 'ovds', 'figures')
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_dir = os.path.join(generated_dir, f'audit_visualization_{timestamp}')
os.makedirs(output_dir, exist_ok=True)
print(f"输出目录: {output_dir}/")

# 读取数据
with open(os.path.join(PROJECT_ROOT, 'results', 'ovds', 'raw', 'eva_audit_results.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取数据
results = data['results']
audit_sizes = [item['audit_size'] for item in results]
audit_means = [item['audit_time']['mean'] for item in results]
audit_stds = [item['audit_time']['std'] for item in results]
judge_means = [item['judge_time']['mean'] for item in results]
judge_stds = [item['judge_time']['std'] for item in results]

# ========== 图表1: 审计和判断时间随审计挑战集大小的变化 ==========
def plot_audit_judge_times():
    """绘制审计和判断时间随审计挑战集大小的变化"""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # 绘制 Audit 线（蓝色，三角形标记）
    ax.plot(audit_sizes, audit_means, 
           marker='^', markersize=10, linewidth=2, 
           color='#1f77b4', label='Audit', 
           markerfacecolor='none', markeredgewidth=2)
    
    # 绘制 Judge 线（橙色，星形标记）
    ax.plot(audit_sizes, judge_means, 
           marker='*', markersize=12, linewidth=2, 
           color='#ff7f0e', label='Judge',
           markerfacecolor='none', markeredgewidth=2)
    
    # 设置坐标轴
    ax.set_xlabel('The size of auditing challenge set', fontsize=12, fontweight='bold')
    ax.set_ylabel('The average running time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('The average running time (ms)', fontsize=14, fontweight='bold')
    
    # 设置坐标轴范围
    ax.set_xlim(150, 1050)
    ax.set_ylim(250, 1050)
    
    # 设置刻度
    ax.set_xticks([200, 400, 600, 800, 1000])
    ax.set_yticks([300, 400, 500, 600, 700, 800, 900, 1000])
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # 添加图例
    ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'audit_judge_times.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表2: 带误差棒的审计和判断时间 ==========
def plot_audit_judge_times_with_errorbars():
    """绘制带误差棒的审计和判断时间"""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # 绘制 Audit 线（蓝色，三角形标记，带误差棒）
    ax.errorbar(audit_sizes, audit_means, yerr=audit_stds,
               marker='^', markersize=10, linewidth=2, 
               color='#1f77b4', label='Audit',
               markerfacecolor='none', markeredgewidth=2,
               capsize=5, capthick=2, elinewidth=1.5)
    
    # 绘制 Judge 线（橙色，星形标记，带误差棒）
    ax.errorbar(audit_sizes, judge_means, yerr=judge_stds,
               marker='*', markersize=12, linewidth=2, 
               color='#ff7f0e', label='Judge',
               markerfacecolor='none', markeredgewidth=2,
               capsize=5, capthick=2, elinewidth=1.5)
    
    # 设置坐标轴
    ax.set_xlabel('The size of auditing challenge set', fontsize=12, fontweight='bold')
    ax.set_ylabel('The average running time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('The average running time (ms) with Error Bars', fontsize=14, fontweight='bold')
    
    # 设置坐标轴范围
    ax.set_xlim(150, 1050)
    ax.set_ylim(200, 1800)
    
    # 设置刻度
    ax.set_xticks([200, 400, 600, 800, 1000])
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # 添加图例
    ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'audit_judge_times_with_errorbars.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表3: 统计信息对比 ==========
def plot_statistics_comparison():
    """绘制统计信息对比（均值、最小值、最大值）"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 左图：Audit 统计信息
    ax1 = axes[0]
    audit_mins = [item['audit_time']['min'] for item in results]
    audit_maxs = [item['audit_time']['max'] for item in results]
    
    ax1.plot(audit_sizes, audit_means, marker='o', label='Mean', linewidth=2, markersize=8)
    ax1.plot(audit_sizes, audit_mins, marker='v', label='Min', linewidth=1.5, markersize=6, linestyle='--', alpha=0.7)
    ax1.plot(audit_sizes, audit_maxs, marker='^', label='Max', linewidth=1.5, markersize=6, linestyle='--', alpha=0.7)
    
    ax1.set_xlabel('The size of auditing challenge set', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Running time (ms)', fontsize=11, fontweight='bold')
    ax1.set_title('Audit Time Statistics', fontsize=12, fontweight='bold')
    ax1.set_xticks([200, 400, 600, 800, 1000])
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(fontsize=10)
    
    # 右图：Judge 统计信息
    ax2 = axes[1]
    judge_mins = [item['judge_time']['min'] for item in results]
    judge_maxs = [item['judge_time']['max'] for item in results]
    
    ax2.plot(audit_sizes, judge_means, marker='o', label='Mean', linewidth=2, markersize=8, color='#ff7f0e')
    ax2.plot(audit_sizes, judge_mins, marker='v', label='Min', linewidth=1.5, markersize=6, linestyle='--', alpha=0.7, color='#ff7f0e')
    ax2.plot(audit_sizes, judge_maxs, marker='^', label='Max', linewidth=1.5, markersize=6, linestyle='--', alpha=0.7, color='#ff7f0e')
    
    ax2.set_xlabel('The size of auditing challenge set', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Running time (ms)', fontsize=11, fontweight='bold')
    ax2.set_title('Judge Time Statistics', fontsize=12, fontweight='bold')
    ax2.set_xticks([200, 400, 600, 800, 1000])
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(fontsize=10)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'statistics_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表4: 性能对比（Audit vs Judge） ==========
def plot_performance_comparison():
    """绘制 Audit 和 Judge 的性能对比"""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    x = np.arange(len(audit_sizes))
    width = 0.35
    
    # 绘制柱状图
    bars1 = ax.bar(x - width/2, audit_means, width, label='Audit', 
                   color='#1f77b4', alpha=0.8, yerr=audit_stds, capsize=5)
    bars2 = ax.bar(x + width/2, judge_means, width, label='Judge', 
                   color='#ff7f0e', alpha=0.8, yerr=judge_stds, capsize=5)
    
    ax.set_xlabel('The size of auditing challenge set', fontsize=12, fontweight='bold')
    ax.set_ylabel('The average running time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('Performance Comparison: Audit vs Judge', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(audit_sizes)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'performance_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

if __name__ == '__main__':
    print("开始生成图表...")
    plot_audit_judge_times()
    plot_audit_judge_times_with_errorbars()
    plot_statistics_comparison()
    plot_performance_comparison()
    print(f"所有图表生成完成！输出目录: {output_dir}/")
    print(f"\n数据集大小: {data['dataset_size']}")
    print(f"Setup 时间: {data['setup_time']:.2f}ms")
    print(f"Append 时间: {data['append_time']:.2f}ms")





