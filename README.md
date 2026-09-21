# OVDS reproduction

本仓库复现并扩展 OVDS（Optimal Verifiable Data Streaming Under Concurrent Queries）实验实现。代码用于验证基于 BLS 签名与 RSA 累加器的数据流追加、查询、更新、审计和证明验证流程及性能测试。

## 复现对象

- 论文：Optimal Verifiable Data Streaming Under Concurrent Queries（DOI: [10.1109/TMC.2023.3309270](https://ieeexplore.ieee.org/abstract/document/10232858)）。
- 参考实现：本项目以公开算法描述和参考仓库为基线，在 `src/vads_lib.py` 中实现 VADS 主流程，并在此基础上整理 OVDS 实验脚本。

## 依赖与原论文仓库

- [Charm-Crypto](https://github.com/JHUISI/charm)：双线性配对、BLS 签名等密码学原语；其原论文/项目仓库为 [JHUISI/charm](https://github.com/JHUISI/charm)。
- [RSA-accumulator](https://github.com/oleiba/RSA-accumulator)：强 RSA 假设下的动态 RSA 累加器及成员/非成员证明；本地代码位于 `RSA-accumulator/`。

Python 依赖见 [`requirements.txt`](requirements.txt)。RSA 累加器的 Node.js 测试依赖见 `RSA-accumulator/package.json`。

## 主要算法

1. `Setup` 初始化 BLS 配对群、密钥、RSA 模数和初始累加器状态。
2. `Append` 对数据块计算标签和 BLS 签名，并更新 RSA 累加器；服务器保存数据与认证状态。
3. `Query/Query*` 生成单块或批量查询证明，包含签名聚合、标签和累加器证明分量。
4. `Verify/Verify*` 验证签名、数据标签、聚合证明及 RSA 累加器关系。
5. `Update` 处理数据流更新；`Audit/Judge` 生成并核验审计证明，覆盖已撤销集合和当前累加器状态。

核心密码层入口为 `src/vads_lib.py`；`src/additional/` 下的 AVDS/CLVC 模块是独立对比实验，不属于 OVDS 主流程。

## 复现工作与差异

- 对参考 RSA 累加器实现进行本地集成，补充 VADS 的 BLS 标签、数据流状态和审计接口。
- 将单条查询扩展为批量/星号查询，并补充追加、更新、审计、证明大小和存储成本实验脚本。
- 对原始流程进行工程化整理：显式维护 `Acc_0`、`Acc_R`、撤销集合和服务端缓存，统一证明验证入口。
- `RSA-accumulator/` 保留参考仓库代码；本仓库新增或修改的实现集中在 `src/`、测试和实验脚本中。详细设计文档保留在工作区，但按发布约定不随 Git 推送（根目录本 README 除外）。

## 运行

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s src/test
python src/main.py
```

Charm-Crypto 可能需要按其官方说明从源码安装；RSA 累加器的 Node.js 基准测试在 `RSA-accumulator/` 中单独运行。

## 分支约定

- `main`：仓库介绍与复现说明。
- `ovds`：本地 OVDS 代码、实验数据和测试；除根目录 `README.md` 外不提交 Markdown 文件。

## 性能测试与可视化目录

- `benchmarks/ovds/performance/`：OVDS 追加、审计、数据大小、存储成本和并发性能测试。
- `benchmarks/ovds/visualization/`：OVDS 性能结果绘图脚本。
- `benchmarks/rsa_accumulator/performance/`：RSA 累加器与 Merkle Tree 对比基准。
- `benchmarks/rsa_accumulator/visualization/`：RSA 累加器基准结果绘图脚本。
- `results/ovds/raw/`、`results/rsa_accumulator/raw/`：JSON/CSV 原始结果。
- `results/ovds/figures/`、`results/rsa_accumulator/figures/`：PNG 图表。

脚本使用自身位置计算项目根目录，可从仓库根目录或脚本所在目录运行。例如：

```bash
python benchmarks/ovds/visualization/visualize_results.py
python benchmarks/ovds/visualization/visualize_audit_results.py
python benchmarks/rsa_accumulator/visualization/visualize_performance.py
```
