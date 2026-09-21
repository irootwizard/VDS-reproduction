"""
根据 results_all.json 生成可视化图表
按照参考图样式：使用线性Y轴，扩大Y轴范围以减小视觉波动
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
output_dir = os.path.join(generated_dir, f'visualization_{timestamp}')
os.makedirs(output_dir, exist_ok=True)
print(f"输出目录: {output_dir}/")

# 读取数据
with open(os.path.join(PROJECT_ROOT, 'results', 'ovds', 'raw', 'results_all2.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取数据
dataset_sizes = [item['dataset_size'] for item in data]

# 时间指标列表
time_metrics = [
    'setup_time', 'append_time', 'query_time', 'verify_time',
    'query_star_time', 'verify_star_time', 'audit_time', 'judge_time', 'update_time'
]

# 证明大小指标列表
proof_size_metrics = ['query_proof_size', 'query_star_proof_size']

# ========== 图表1: 主要查询和验证时间 ==========
def plot_query_verify_times():
    """绘制查询和验证相关的时间指标 - 使用线性Y轴，扩大范围"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    metrics_to_plot = ['query_time', 'verify_time', 'query_star_time', 'verify_star_time']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    markers = ['o', 's', '^', 'v']
    
    for i, metric in enumerate(metrics_to_plot):
        means = [item[metric]['mean'] for item in data]
        stds = [item[metric]['std'] for item in data]
        
        ax.errorbar(dataset_sizes, means, yerr=stds, 
                   marker=markers[i], label=metric.replace('_', ' ').title(),
                   color=colors[i], linewidth=2, markersize=8, capsize=5, capthick=2)
    
    ax.set_xlabel('数据集大小', fontsize=12, fontweight='bold')
    ax.set_ylabel('时间 (ms)', fontsize=12, fontweight='bold')
    ax.set_title('查询和验证时间随数据集大小的变化', fontsize=14, fontweight='bold')
    ax.set_xscale('log', base=2)
    # 使用线性Y轴，设置较大的范围以减小视觉波动
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=10, loc='best')
    ax.set_xticks(dataset_sizes)
    ax.set_xticklabels(dataset_sizes)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'query_verify_times.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表2: 审计和判断时间 ==========
def plot_audit_judge_times():
    """绘制审计和判断相关的时间指标 - 使用线性Y轴，扩大范围"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    metrics_to_plot = ['audit_time', 'judge_time']
    colors = ['#9467bd', '#8c564b']
    markers = ['o', 's']
    
    for i, metric in enumerate(metrics_to_plot):
        means = [item[metric]['mean'] for item in data]
        stds = [item[metric]['std'] for item in data]
        
        ax.errorbar(dataset_sizes, means, yerr=stds,
                   marker=markers[i], label=metric.replace('_', ' ').title(),
                   color=colors[i], linewidth=2, markersize=8, capsize=5, capthick=2)
    
    ax.set_xlabel('数据集大小', fontsize=12, fontweight='bold')
    ax.set_ylabel('时间 (ms)', fontsize=12, fontweight='bold')
    ax.set_title('审计和判断时间随数据集大小的变化', fontsize=14, fontweight='bold')
    ax.set_xscale('log', base=2)
    # 使用线性Y轴，设置较大的范围以减小视觉波动
    ax.set_ylim(0, 150)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=10, loc='best')
    ax.set_xticks(dataset_sizes)
    ax.set_xticklabels(dataset_sizes)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'audit_judge_times.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表3: 所有时间指标对比 ==========
def plot_all_times():
    """绘制所有时间指标的对比 - 使用线性Y轴，扩大范围"""
    fig, axes = plt.subplots(3, 3, figsize=(18, 15))
    axes = axes.flatten()
    
    # 为每个指标设置合适的Y轴范围
    y_limits = {
        'setup_time': (0, 1500),
        'append_time': (0, 50),
        'query_time': (0, 100),
        'verify_time': (0, 50),
        'query_star_time': (0, 50),
        'verify_star_time': (0, 100),
        'audit_time': (0, 150),
        'judge_time': (0, 200),
        'update_time': (0, 200)
    }
    
    for idx, metric in enumerate(time_metrics):
        ax = axes[idx]
        means = [item[metric]['mean'] for item in data]
        stds = [item[metric]['std'] for item in data]
        
        ax.errorbar(dataset_sizes, means, yerr=stds,
                   marker='o', color='#1f77b4', linewidth=2, markersize=6, capsize=4)
        
        ax.set_xlabel('数据集大小', fontsize=10)
        ax.set_ylabel('时间 (ms)', fontsize=10)
        ax.set_title(metric.replace('_', ' ').title(), fontsize=11, fontweight='bold')
        ax.set_xscale('log', base=2)
        # 使用线性Y轴，根据指标设置合适的范围
        if metric in y_limits:
            ax.set_ylim(y_limits[metric])
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xticks(dataset_sizes)
        ax.set_xticklabels(dataset_sizes, rotation=45, ha='right')
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'all_times.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表4: 证明大小 ==========
def plot_proof_sizes():
    """绘制证明大小随数据集大小的变化 - 使用线性Y轴，扩大范围"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = ['#1f77b4', '#ff7f0e']
    markers = ['o', 's']
    
    for i, metric in enumerate(proof_size_metrics):
        means = [item[metric]['mean'] for item in data]
        stds = [item[metric]['std'] for item in data]
        
        ax.errorbar(dataset_sizes, means, yerr=stds,
                   marker=markers[i], label=metric.replace('_', ' ').title(),
                   color=colors[i], linewidth=2, markersize=8, capsize=5, capthick=2)
    
    ax.set_xlabel('数据集大小', fontsize=12, fontweight='bold')
    ax.set_ylabel('证明大小 (字节)', fontsize=12, fontweight='bold')
    ax.set_title('证明大小随数据集大小的变化', fontsize=14, fontweight='bold')
    ax.set_xscale('log', base=2)
    # 使用线性Y轴，设置较大的范围以减小视觉波动（转换为KB显示）
    # 数据范围约64-621字节，设置0-1000字节或0-1KB
    ax.set_ylim(0, 1000)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=10, loc='best')
    ax.set_xticks(dataset_sizes)
    ax.set_xticklabels(dataset_sizes)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'proof_sizes.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()
    
# ========== 图表5: 综合性能对比（主要指标） ==========
def plot_main_metrics():
    """绘制主要性能指标的综合对比 - 使用线性Y轴，扩大范围"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 左图：查询相关时间
    query_metrics = ['query_time', 'query_star_time']
    colors1 = ['#1f77b4', '#2ca02c']
    markers1 = ['o', '^']
    
    for i, metric in enumerate(query_metrics):
        means = [item[metric]['mean'] for item in data]
        stds = [item[metric]['std'] for item in data]
        ax1.errorbar(dataset_sizes, means, yerr=stds,
                    marker=markers1[i], label=metric.replace('_', ' ').title(),
                    color=colors1[i], linewidth=2, markersize=8, capsize=5)
    
    ax1.set_xlabel('数据集大小', fontsize=11, fontweight='bold')
    ax1.set_ylabel('时间 (ms)', fontsize=11, fontweight='bold')
    ax1.set_title('查询时间对比', fontsize=12, fontweight='bold')
    ax1.set_xscale('log', base=2)
    ax1.set_ylim(0, 50)  # 使用线性Y轴
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(fontsize=10)
    ax1.set_xticks(dataset_sizes)
    ax1.set_xticklabels(dataset_sizes)
    
    # 右图：验证相关时间
    verify_metrics = ['verify_time', 'verify_star_time']
    colors2 = ['#ff7f0e', '#d62728']
    markers2 = ['s', 'v']
    
    for i, metric in enumerate(verify_metrics):
        means = [item[metric]['mean'] for item in data]
        stds = [item[metric]['std'] for item in data]
        ax2.errorbar(dataset_sizes, means, yerr=stds,
                    marker=markers2[i], label=metric.replace('_', ' ').title(),
                    color=colors2[i], linewidth=2, markersize=8, capsize=5)
    
    ax2.set_xlabel('数据集大小', fontsize=11, fontweight='bold')
    ax2.set_ylabel('时间 (ms)', fontsize=11, fontweight='bold')
    ax2.set_title('验证时间对比', fontsize=12, fontweight='bold')
    ax2.set_xscale('log', base=2)
    ax2.set_ylim(0, 100)  # 使用线性Y轴
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(fontsize=10)
    ax2.set_xticks(dataset_sizes)
    ax2.set_xticklabels(dataset_sizes)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'main_metrics.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表6: 更新和追加时间 ==========
def plot_update_append_times():
    """绘制更新和追加时间 - 使用线性Y轴，扩大范围"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    metrics_to_plot = ['append_time', 'update_time']
    colors = ['#17becf', '#bcbd22']
    markers = ['o', 's']
    
    for i, metric in enumerate(metrics_to_plot):
        means = [item[metric]['mean'] for item in data]
        stds = [item[metric]['std'] for item in data]
        
        ax.errorbar(dataset_sizes, means, yerr=stds,
                   marker=markers[i], label=metric.replace('_', ' ').title(),
                   color=colors[i], linewidth=2, markersize=8, capsize=5, capthick=2)
    
    ax.set_xlabel('数据集大小', fontsize=12, fontweight='bold')
    ax.set_ylabel('时间 (ms)', fontsize=12, fontweight='bold')
    ax.set_title('追加和更新时间随数据集大小的变化', fontsize=14, fontweight='bold')
    ax.set_xscale('log', base=2)
    # 使用线性Y轴，设置较大的范围以减小视觉波动
    ax.set_ylim(0, 200)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=10, loc='best')
    ax.set_xticks(dataset_sizes)
    ax.set_xticklabels(dataset_sizes)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'update_append_times.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

if __name__ == '__main__':
    print("开始生成图表...")
    plot_query_verify_times()
    plot_audit_judge_times()
    plot_all_times()
    plot_proof_sizes()
    plot_main_metrics()
    plot_update_append_times()
    print(f"所有图表生成完成！输出目录: {output_dir}/")
