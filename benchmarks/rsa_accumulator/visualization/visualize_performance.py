"""
RSA Accumulator vs Merkle Tree 性能对比可视化
基于generated目录中的实际测试数据
"""
import matplotlib.pyplot as plt
import numpy as np
import csv
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
GENERATED_DIR = os.path.join(PROJECT_ROOT, 'results', 'rsa_accumulator', 'raw')
FIGURES_DIR = os.path.join(PROJECT_ROOT, 'results', 'rsa_accumulator', 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

# ========== 数据读取函数 ==========
def read_csv_data(filename):
    """从CSV文件读取数据，返回字典格式"""
    data = {}
    if not os.path.exists(filename):
        print(f"警告: 文件 {filename} 不存在")
        return None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) < 2:
                return None
            
            # 从第二行开始是数据行（跳过第一行的列名和可能的注释行）
            for row in rows[1:]:
                if len(row) > 0 and row[0].strip():
                    key = row[0].strip()
                    # 跳过注释行和空行
                    if key.startswith('#') or not key:
                        continue
                    values = []
                    for val in row[1:]:
                        try:
                            if val.strip():
                                values.append(float(val.strip()))
                        except ValueError:
                            pass
                    if values:
                        data[key] = values
        return data if data else None
    except Exception as e:
        print(f"读取 {filename} 时出错: {e}")
        return None

# ========== 图表1: 证明生成性能对比 ==========
def plot_figure1_proof_generation():
    """证明生成性能对比：Merkle Tree vs RSA Accumulator"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    proofs_data = read_csv_data(os.path.join(GENERATED_DIR, 'proofs-per-tx.csv'))
    
    if not proofs_data:
        print("无法读取证明生成数据")
        return
    
    x_values = [20, 40, 60, 80, 100]
    
    # 转换为毫秒
    if 'Merkle Tree' in proofs_data:
        merkle_times = [t * 1000 for t in proofs_data['Merkle Tree']]
        ax.plot(x_values, merkle_times, 'o-', color='blue', label='Merkle Tree', 
                markersize=8, linewidth=2)
    
    if 'Accumulator: Aggregate' in proofs_data:
        acc_agg_times = [t * 1000 for t in proofs_data['Accumulator: Aggregate']]
        ax.plot(x_values, acc_agg_times, 's-', color='green', label='RSA Accumulator: Aggregate', 
                markersize=8, linewidth=2)
    
    if 'Accumulator: Aggregate w. NI-PoE' in proofs_data:
        acc_niope_times = [t * 1000 for t in proofs_data['Accumulator: Aggregate w. NI-PoE']]
        ax.plot(x_values, acc_niope_times, '^-', color='orange', label='RSA Accumulator: Aggregate w. NI-PoE', 
                markersize=8, linewidth=2)
    
    ax.set_xlabel('每块交易数量', fontsize=12)
    ax.set_ylabel('平均运行时间 (ms)', fontsize=12)
    ax.set_title('证明生成性能对比', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    
    plt.tight_layout()
    output_path = os.path.join(FIGURES_DIR, 'figure1_proof_generation.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表2: 验证性能对比（每交易） ==========
def plot_figure2_verify_per_tx():
    """验证性能对比：每交易"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    verify_data = read_csv_data(os.path.join(GENERATED_DIR, 'verifications-per-tx.csv'))
    
    if not verify_data:
        print("无法读取验证数据")
        return
    
    x_values = [20, 40, 60, 80, 100]
    
    # 转换为毫秒
    if 'Merkle Tree' in verify_data:
        merkle_times = [t * 1000 for t in verify_data['Merkle Tree']]
        ax.plot(x_values, merkle_times, 'o-', color='blue', label='Merkle Tree', 
                markersize=8, linewidth=2)
    
    if 'Accumulator: Batch' in verify_data:
        acc_batch_times = [t * 1000 for t in verify_data['Accumulator: Batch']]
        ax.plot(x_values, acc_batch_times, 's-', color='green', label='RSA Accumulator: Batch', 
                markersize=8, linewidth=2)
    
    if 'Accumulator: Batch w. NI-PoE' in verify_data:
        acc_niope_times = [t * 1000 for t in verify_data['Accumulator: Batch w. NI-PoE']]
        ax.plot(x_values, acc_niope_times, '^-', color='orange', label='RSA Accumulator: Batch w. NI-PoE', 
                markersize=8, linewidth=2)
    
    ax.set_xlabel('每块交易数量', fontsize=12)
    ax.set_ylabel('平均运行时间 (ms)', fontsize=12)
    ax.set_title('验证性能对比（每交易）', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    
    plt.tight_layout()
    output_path = os.path.join(FIGURES_DIR, 'figure2_verify_per_tx.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表3: 验证性能对比（每块） ==========
def plot_figure3_verify_per_block():
    """验证性能对比：每块"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    verify_data = read_csv_data(os.path.join(GENERATED_DIR, 'verifications-per-block.csv'))
    
    if not verify_data:
        print("无法读取验证数据")
        return
    
    x_values = [20, 40, 60, 80, 100]
    
    # 转换为毫秒
    if 'Merkle Tree' in verify_data:
        merkle_times = [t * 1000 for t in verify_data['Merkle Tree']]
        ax.plot(x_values, merkle_times, 'o-', color='blue', label='Merkle Tree', 
                markersize=8, linewidth=2)
    
    if 'Accumulator: Batch' in verify_data:
        acc_batch_times = [t * 1000 for t in verify_data['Accumulator: Batch']]
        ax.plot(x_values, acc_batch_times, 's-', color='green', label='RSA Accumulator: Batch', 
                markersize=8, linewidth=2)
    
    if 'Accumulator: Batch w. NI-PoE' in verify_data:
        acc_niope_times = [t * 1000 for t in verify_data['Accumulator: Batch w. NI-PoE']]
        ax.plot(x_values, acc_niope_times, '^-', color='orange', label='RSA Accumulator: Batch w. NI-PoE', 
                markersize=8, linewidth=2)
    
    ax.set_xlabel('每块交易数量', fontsize=12)
    ax.set_ylabel('平均运行时间 (ms)', fontsize=12)
    ax.set_title('验证性能对比（每块）', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    
    plt.tight_layout()
    output_path = os.path.join(FIGURES_DIR, 'figure3_verify_per_block.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表4: 批量操作性能 ==========
def plot_figure4_batch_operations():
    """批量操作性能：Batch Add vs Batch Delete"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    add_data = read_csv_data(os.path.join(GENERATED_DIR, 'batch-add-per-block.csv'))
    delete_data = read_csv_data(os.path.join(GENERATED_DIR, 'batch-delete-per-block.csv'))
    
    if not add_data and not delete_data:
        print("无法读取批量操作数据")
        return
    
    x_values = [20, 40, 60, 80, 100]
    
    # 转换为毫秒
    if add_data and 'Accumulator: Batch Add' in add_data:
        add_times = [t * 1000 for t in add_data['Accumulator: Batch Add']]
        ax.plot(x_values, add_times, 'o-', color='teal', label='RSA Accumulator: Batch Add', 
                markersize=8, linewidth=2)
    
    if delete_data and 'Accumulator: Batch Delete' in delete_data:
        delete_times = [t * 1000 for t in delete_data['Accumulator: Batch Delete']]
        ax.plot(x_values, delete_times, 's-', color='red', label='RSA Accumulator: Batch Delete', 
                markersize=8, linewidth=2)
    
    ax.set_xlabel('每块交易数量', fontsize=12)
    ax.set_ylabel('平均运行时间 (ms)', fontsize=12)
    ax.set_title('批量操作性能对比', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    
    plt.tight_layout()
    output_path = os.path.join(FIGURES_DIR, 'figure4_batch_operations.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表5: NI-PoE验证性能 ==========
def plot_figure5_niope_verification():
    """NI-PoE验证性能：验证两个NI-PoE证明"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    niope_data = read_csv_data(os.path.join(GENERATED_DIR, 'batch-verify-aggregated-two-niopes.csv'))
    
    if not niope_data:
        print("无法读取NI-PoE验证数据")
        return
    
    x_values = [20, 40, 60, 80, 100]
    
    # 转换为毫秒
    if 'Accumulator: Verify 2 NIPoEs' in niope_data:
        niope_times = [t * 1000 for t in niope_data['Accumulator: Verify 2 NIPoEs']]
        ax.plot(x_values, niope_times, 'o-', color='purple', label='RSA Accumulator: Verify 2 NIPoEs', 
                markersize=8, linewidth=2)
    
    ax.set_xlabel('每块交易数量', fontsize=12)
    ax.set_ylabel('平均运行时间 (ms)', fontsize=12)
    ax.set_title('NI-PoE验证性能', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    
    plt.tight_layout()
    output_path = os.path.join(FIGURES_DIR, 'figure5_niope_verification.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 图表6: 综合性能对比（三合一） ==========
def plot_figure6_comprehensive_comparison():
    """综合性能对比：证明生成、验证（per tx）、批量操作"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    proofs_data = read_csv_data(os.path.join(GENERATED_DIR, 'proofs-per-tx.csv'))
    verify_data = read_csv_data(os.path.join(GENERATED_DIR, 'verifications-per-tx.csv'))
    add_data = read_csv_data(os.path.join(GENERATED_DIR, 'batch-add-per-block.csv'))
    delete_data = read_csv_data(os.path.join(GENERATED_DIR, 'batch-delete-per-block.csv'))
    
    x_values = [20, 40, 60, 80, 100]
    
    # 子图1: 证明生成
    ax1 = axes[0]
    if proofs_data:
        if 'Merkle Tree' in proofs_data:
            merkle_times = [t * 1000 for t in proofs_data['Merkle Tree']]
            ax1.plot(x_values, merkle_times, 'o-', color='blue', label='Merkle Tree', 
                    markersize=6, linewidth=2)
        if 'Accumulator: Aggregate' in proofs_data:
            acc_times = [t * 1000 for t in proofs_data['Accumulator: Aggregate']]
            ax1.plot(x_values, acc_times, 's-', color='green', label='RSA Accumulator', 
                    markersize=6, linewidth=2)
    ax1.set_xlabel('每块交易数量', fontsize=11)
    ax1.set_ylabel('平均运行时间 (ms)', fontsize=11)
    ax1.set_title('(a) 证明生成', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)
    
    # 子图2: 验证（per tx）
    ax2 = axes[1]
    if verify_data:
        if 'Merkle Tree' in verify_data:
            merkle_times = [t * 1000 for t in verify_data['Merkle Tree']]
            ax2.plot(x_values, merkle_times, 'o-', color='blue', label='Merkle Tree', 
                    markersize=6, linewidth=2)
        if 'Accumulator: Batch' in verify_data:
            acc_times = [t * 1000 for t in verify_data['Accumulator: Batch']]
            ax2.plot(x_values, acc_times, 's-', color='green', label='RSA Accumulator', 
                    markersize=6, linewidth=2)
    ax2.set_xlabel('每块交易数量', fontsize=11)
    ax2.set_ylabel('平均运行时间 (ms)', fontsize=11)
    ax2.set_title('(b) 验证（每交易）', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)
    
    # 子图3: 批量操作
    ax3 = axes[2]
    if add_data and 'Accumulator: Batch Add' in add_data:
        add_times = [t * 1000 for t in add_data['Accumulator: Batch Add']]
        ax3.plot(x_values, add_times, 'o-', color='teal', label='Batch Add', 
                markersize=6, linewidth=2)
    if delete_data and 'Accumulator: Batch Delete' in delete_data:
        delete_times = [t * 1000 for t in delete_data['Accumulator: Batch Delete']]
        ax3.plot(x_values, delete_times, 's-', color='red', label='Batch Delete', 
                markersize=6, linewidth=2)
    ax3.set_xlabel('每块交易数量', fontsize=11)
    ax3.set_ylabel('平均运行时间 (ms)', fontsize=11)
    ax3.set_title('(c) 批量操作', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=9)
    
    plt.tight_layout()
    output_path = os.path.join(FIGURES_DIR, 'figure6_comprehensive_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存: {output_path}")
    plt.close()

# ========== 主函数 ==========
def main():
    """生成所有性能对比图表"""
    # 确保输出目录存在
    os.makedirs(FIGURES_DIR, exist_ok=True)
    
    print("正在生成RSA Accumulator vs Merkle Tree性能对比图表...")
    print("=" * 60)
    print(f"数据来源目录: {GENERATED_DIR}/")
    print("=" * 60)
    
    # 生成所有图表
    plot_figure1_proof_generation()
    plot_figure2_verify_per_tx()
    plot_figure3_verify_per_block()
    plot_figure4_batch_operations()
    plot_figure5_niope_verification()
    plot_figure6_comprehensive_comparison()
    
    print("=" * 60)
    print("所有图表已生成完成！")
    print(f"输出目录: {FIGURES_DIR}/")
    print("\n生成的图表文件：")
    print("  - figure1_proof_generation.png: 证明生成性能对比")
    print("  - figure2_verify_per_tx.png: 验证性能对比（每交易）")
    print("  - figure3_verify_per_block.png: 验证性能对比（每块）")
    print("  - figure4_batch_operations.png: 批量操作性能对比")
    print("  - figure5_niope_verification.png: NI-PoE验证性能")
    print("  - figure6_comprehensive_comparison.png: 综合性能对比")

if __name__ == '__main__':
    main()







