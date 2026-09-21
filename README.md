# Verifiable Data Streaming (VDS) 论文复现

本仓库用于整理和复现 **可验证数据流（Verifiable Data Streaming, VDS）** 方向论文。`main` 分支只保存领域定义、历史研究脉络、论文索引和复现进度；每篇论文的代码与实验放在独立分支。

## VDS 的提出与定义

VDS 由 Schroder 与 Schroder 在 2012 年提出并形式化。其目标是：客户端持续把数据流外包给不可信服务器，服务器保存数据并响应查询；客户端只保留很小的本地状态，但仍能验证服务器返回的数据是否真实、完整、最新，并且没有把旧数据、篡改数据或遗漏数据伪装成合法结果。

一个 VDS 协议通常包含以下算法或接口：

| 接口 | 含义 |
| --- | --- |
| `Setup` | 初始化安全参数、密钥、公开参数和客户端本地状态 |
| `Update/Append` | 向数据流追加或更新元素，并生成认证信息 |
| `Query` | 服务器根据索引、区间、集合或关键词返回数据和证明 |
| `Verify` | 客户端用短状态或验证密钥检查返回结果是否正确 |
| `Audit` | 在部分工作中，用抽查或聚合证明检查服务器是否仍正确保存数据 |

VDS 与相邻概念的区别：

- 与普通认证数据结构相比，VDS 更强调数据以流形式持续到达，客户端不能长期保存全量数据。
- 与 PDP/PoR 相比，VDS 不只证明“服务器还持有数据”，还要支持具体查询结果的正确性验证。
- 与通用可验证计算相比，VDS 的目标通常更具体：围绕外包数据流的追加、查询、更新、审计和批量验证优化。

## 历史研究脉络

早期 VDS 关注单点查询和轻量客户端状态；之后研究逐步扩展到高效证明、批量查询、更新历史、并发查询、关键词查询、动态维护和可撤销数据。整体趋势是从“能验证”走向“在真实查询负载下高效验证”。

| 年份 | 论文 | 核心问题 | 主要技术 |
| --- | --- | --- | --- |
| 2012 | [**Verifiable Data Streaming**](https://doi.org/10.1145/2382196.2382297) | 首次形式化 VDS：客户端将流式数据外包给服务器，同时验证查询结果。 | 认证数据结构、短客户端状态、查询证明、安全模型。 |
| 2013 | [**Publicly Verifiable Grouped Aggregation Queries on Outsourced Data Streams**](https://doi.org/10.1109/ICDE.2013.6544852) | 支持对外包数据流执行可公开验证的分组聚合查询。 | 聚合证明、公开验证、外包数据流查询。 |
| 2015 | [**Efficient Verifiable Data Streaming**](https://doi.org/10.1002/sec.1317) | 降低早期 VDS 的通信、存储和验证开销，使协议更接近实用。 | 更紧凑的认证信息、改进证明结构、数据流查询优化。 |
| 2015 | [**VeriStream: A Framework for Verifiable Data Streaming**](https://doi.org/10.1007/978-3-662-47854-7_34) | 给出面向系统实现的 VDS 框架，让流式外包和验证流程模块化。 | 框架化接口、服务端证明生成、客户端轻量验证。 |
| 2016 | [**Nearly Optimal Verifiable Data Streaming**](https://doi.org/10.1007/978-3-662-49384-7_16) | 追求接近最优的证明大小、更新时间和验证复杂度。 | 更优认证结构、复杂度优化、理论边界分析。 |
| 2017 | [**Dynamic Chameleon Authentication Tree for Verifiable Data Streaming in 5G Networks**](https://doi.org/10.1109/ACCESS.2017.2771281) | 面向 5G 数据流支持动态认证和完整性验证。 | 动态认证树、变色龙哈希、流数据完整性。 |
| 2018 | [**VENUS: Verifiable Range Query in Data Streaming**](https://doi.org/10.1109/INFOCOMW.2018.8406898) | 支持数据流上的可验证范围查询。 | 范围查询、认证数据结构、查询证明。 |
| 2021 | [**Optimal Verifiable Data Streaming Protocol with Data Auditing**](https://doi.org/10.1007/978-3-030-88428-4_15) | 在数据流外包中结合查询验证与数据审计。 | 审计协议、公开验证、认证数据流。 |
| 2021 | [**Verifiable Data Streaming with Efficient Update for Intelligent Automation Systems**](https://doi.org/10.1002/int.22671) | 降低智能自动化场景中数据流更新的验证开销。 | 高效更新、动态认证、自动化数据流。 |
| 2022 | [**New Unbounded Verifiable Data Streaming for Batch Query with Almost Optimal Overhead**](https://doi.org/10.1007/978-3-031-17140-6_17) | 支持无界数据流的批量查询，并降低整体开销。 | 批量查询、无界流、近最优复杂度。 |
| 2022 | [**Verifiable Data Streaming Protocol Supporting Update History Queries**](https://doi.org/10.1002/int.23045) | 支持对数据更新历史进行可验证查询。 | 更新历史、动态认证、历史查询证明。 |
| 2024 | [**Optimal Verifiable Data Streaming Under Concurrent Queries**](https://doi.org/10.1109/TMC.2023.3309270) | 在并发查询场景下优化 VDS，使多查询同时发生时仍保持高效和可验证。 | 并发查询处理、聚合证明、BLS 签名、RSA 累加器。 |
| 2024 | [**Aggregatably Verifiable Data Streaming**](https://doi.org/10.1109/JIOT.2024.3388448) | 通过可聚合证明降低多次数据流验证的开销。 | 聚合证明、向量承诺、公开验证。 |
| 2024 | [**Blockchain-Based Compact Verifiable Data Streaming with Self-Auditing**](https://doi.org/10.1109/TDSC.2023.3340208) | 在区块链场景中压缩 VDS 证明并支持自审计。 | 区块链、紧凑证明、自审计。 |
| 2025 | [**Low-Storage Verifiable Data Streaming With Efficient Revocation Approach**](https://doi.org/10.1109/TC.2025.3604531) | 在较低存储开销下支持可验证数据流撤销。 | 低存储认证、撤销机制、动态验证。 |
| 2025 | [**Toward Efficient Verifiable Data Streaming Without Cryptographic Accumulator**](https://doi.org/10.1109/TMC.2025.3582087) | 探索不依赖密码学累加器的高效 VDS 构造。 | 无累加器设计、验证优化、数据流认证。 |
| 2025 | [**Maintainable Verifiable Data Streaming Based on Redactable Blockchain**](https://doi.org/10.1016/j.csi.2025.103972) | 降低长期运行中的状态更新、证明刷新和维护成本。 | 可维护认证结构、可编辑区块链、状态维护。 |
| 2026 | [**Verifiable Data Streaming Protocol Supporting Keyword Queries**](https://doi.org/10.1109/TNSM.2025.3629071) | 支持关键词查询，而不是只按位置、索引或范围查询。 | 关键词索引、认证查询、可验证检索证明。 |

## 论文复现进度

| 论文 | 分支 | 状态 | 说明 |
| --- | --- | --- | --- |
|  |  |  |  |

## 分支约定

- `main`：只保存 VDS 定义、研究脉络、论文列表和复现进度。
- 每篇论文使用独立分支。
- 已开源论文优先对照原实现复现；未开源论文按论文算法独立实现，并记录推断假设。
- 每个论文分支包含代码、测试、基准、原始结果和复现说明。


