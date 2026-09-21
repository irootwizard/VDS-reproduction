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

核心密码层入口为 `src/vads_lib.py`

## 核心算法与公式

### 符号表

| 符号 | 代码变量 | 含义 |
|---|---|---|
| $`\lambda`$ | `SECURITY_PARAM = 128` | 安全参数 |
| $`n`$ | `vk['n']` | RSA 模数（3072 bit） |
| $`h`$ | `vk['h']` | RSA 累加器初始值 $`\text{Acc}(\emptyset)`$ |
| $`\text{Acc}_R`$ | `server_state['Acc_R']` | 当前累加器值，对应撤销集合 $`R`$ |
| $`z^\ast`$ | `server_state['z_star']` | $`\prod_{t_j \in R} H_{\text{prime}}(t_j)`$，缓存的素数积 |
| $`z_i`$ | 局部变量 `z_i` | $`H_{\text{prime}}(\mathit{tag}_i)`$，单个 tag 的素数映射 |
| $`\alpha`$ | `sk['alpha']` | BLS 私钥，$`\alpha \in \mathbb{Z}_p`$ |
| $`g`$ | `vk['g']` | $`\mathbb{G}_2`$ 生成元 |
| $`A`$ | `vk['A']` | BLS 公钥，$`A = g^\alpha \in \mathbb{G}_2`$ |
| $`u`$ | `vk['u']` | 随机基点，$`u \in \mathbb{G}_1`$ |
| $`\sigma_i`$ | `sigma_i` | 数据块 $`s_i`$ 的 BLS 签名 |
| $`\mathit{tag}_i`$ | `tag_i` | 数据块的随机标签，$`\mathit{tag}_i \in \{0,1\}^\lambda`$ |
| $`H_G`$ | `vk['HG']` | 哈希函数 $`H_G: \{0,1\}^\ast \to \mathbb{G}_1`$ |
| $`H_{\text{prime}}`$ | `vk['HPrime']` | 哈希函数 $`H_{\text{prime}}: \{0,1\}^\ast \to \text{Primes}(\lambda)`$ |
| $`H_\lambda`$ | `H_2` | 哈希函数 $`H_\lambda: \{0,1\}^\ast \to [0, 2^\lambda)`$ |
| $`H_{\text{Primes}}`$ | `H_Primes` | 哈希函数 $`H_{\text{Primes}}: \{0,1\}^\ast \to \text{Primes}(\lambda)`$，用于 Fiat-Shamir |

---

### Setup

初始化双线性配对群与 RSA 累加器：

$$n, h \leftarrow \text{RSA.Setup}(1^\lambda), \quad g \xleftarrow{R} \mathbb{G}_2, \quad u \xleftarrow{R} \mathbb{G}_1, \quad \alpha \xleftarrow{R} \mathbb{Z}_p$$

$$A = g^\alpha \in \mathbb{G}_2, \quad \text{Acc}(\emptyset) = h$$

```python
# vads_lib.py:366
n, A0, S = accumulator_setup()   # h = A0
alpha = group.random(ZR)
A = g ** alpha
```

---

### Append

**Client** 对第 $`i`$ 条数据 $`s_i`$ 生成 BLS 签名：

$$\sigma_i = \bigl(H_G(i \| \mathit{tag}_i) \cdot u^{s_i}\bigr)^\alpha \in \mathbb{G}_1$$

**Server** 验证后存储 $`(s_i, \sigma_i, \mathit{tag}_i)`$，验证条件：

$$e(\sigma_i,\ g) = e\!\left(H_G(i \| \mathit{tag}_i) \cdot u^{s_i},\ A\right)$$

```python
# vads_lib.py:475
sigma_i = (HG(str(i) + str(tag_i)) * u ** s) ** alpha
# 验证：pair(sigma_i, g) == pair(HG_i_tag * u_s, A)
```

---

### Query（单查询非成员证明）

**目标**：证明 $`\mathit{tag}_i \notin R`$，即数据块 $`s_i`$ 未被撤销。

令 $`z_i = H_{\text{prime}}(\mathit{tag}_i)`$，$`z^\ast = \prod_{t_j \in R} H_{\text{prime}}(t_j)`$。

由于 $`\gcd(z_i, z^\ast) = 1`$，用扩展欧几里得算法求 Bezout 系数：

$$x \cdot z^\ast + y \cdot z_i = 1 \quad (x, y \in \mathbb{Z})$$

计算：

$$Y = h^y \bmod n \quad (\text{若 } y < 0 \text{ 则取 } h^{-1} \text{ 的正幂})$$

证明 $`\pi = (x, Y)`$。

**Verify** 验证条件：

$$\text{Acc}_R^x \cdot Y^{z_i} \equiv h \pmod{n}$$

**正确性**：$`\text{Acc}_R = h^{z^\ast} \bmod n`$，代入得 $`h^{x \cdot z^\ast} \cdot h^{y \cdot z_i} = h^{x z^\ast + y z_i} = h^1 = h`$。

```python
# vads_lib.py:627
x, y = EEA(z_star, z_i)
Y = pow(h, y, n)           # 负数情形取 mul_inv(h, n) 的正幂
# 验证：(Acc_R^x * Y^z_i) % n == h
```

---

### Update

更新第 $`i`$ 条数据为 $`s_i'`$：生成新标签 $`\mathit{tag}_i'`$ 和新签名 $`\sigma_i'`$，将旧 $`\mathit{tag}_i`$ 加入撤销集合：

$$R \leftarrow R \cup \{\mathit{tag}_i\}, \quad z^\ast \leftarrow z^\ast \cdot H_{\text{prime}}(\mathit{tag}_i)$$

$$\text{Acc}_R = h^{z^\ast} \bmod n$$

```python
# vads_lib.py:1222
server_state['R'].add(tag_i)
server_state['z_star'] *= H_prime(tag_i)   # update_z_star
server_state['Acc_R'] = pow(h, z_star, n)
```

---

### Query\* / WitCreate\_star（聚合非成员证明，Algorithm 2）

**目标**：一次证明查询集合 $`Q = \{z_1, \ldots, z_k\}`$（$`z_j = H_{\mathrm{prime}}(\mathit{tag}_j)`$）中所有 tag 均不在 $`R`$ 中。

令 $`\omega' = \prod_{z_i \in Q} z_i`$，由 $`\gcd(z^\ast, \omega') = 1`$ 求：

$$x \cdot z^\ast + y \cdot \omega' = 1$$

**步骤 5–6**：

$$V = \text{Acc}_R^x \bmod n, \quad Y = h^y \bmod n$$

**步骤 7–9**（NI-PoE 子证明 1，对 $`Y`$ 的指数 $`\omega'`$）：

$$l_1 = H_{\text{Primes}}(\omega',\ Y,\ h \cdot V^{-1}), \quad t_1 = \lfloor \omega' / l_1 \rfloor, \quad T_1 = Y^{t_1} \bmod n$$

**步骤 10–16**（NI-PoE 子证明 2，对 $`\text{Acc}_R`$ 的指数 $`x`$）：

$$h' = H_G'(\text{Acc}_R \| V), \quad l_2 = H_{\text{Primes}}(\text{Acc}_R,\ V,\ X'), \quad \gamma = H_\lambda(\text{Acc}_R,\ V,\ X',\ l_2)$$

$$X' = (h')^x \bmod n, \quad t_2 = \lfloor x / l_2 \rfloor, \quad r = x \bmod l_2$$

$$T_2 = \bigl(\text{Acc}_R \cdot (h')^\gamma\bigr)^{t_2} \bmod n$$

证明 $`\pi = \{V, Y, T_1, T_2, X', r\}`$。

**WitVerify\_star** 验证两个条件：

$$T_1^{l_1} \cdot Y^{r'} \equiv h \cdot V^{-1} \pmod{n}, \quad r' = \omega' \bmod l_1$$

$$T_2^{l_2} \cdot \bigl(\text{Acc}_R \cdot (h')^\gamma\bigr)^r \equiv V \cdot (X')^\gamma \pmod{n}$$

```python
# vads_lib.py:167  WitCreate_star
x, y = EEA(z_star, omega_prime)
V = pow(Acc_R, x, n);   Y = pow(h, y, n)
l_1 = H_Primes(omega_prime, Y, (h * mul_inv(V,n)) % n)
T_1 = pow(Y, omega_prime // l_1, n)
h_prime = H_G_prime(concat(Acc_R, V), n)
X_prime = pow(h_prime, x, n)
l_2 = H_Primes(Acc_R, V, X_prime)
gamma = H_2(concat(Acc_R, V, X_prime, l_2))
T_2 = pow((Acc_R * pow(h_prime, gamma, n)) % n, x // l_2, n)
```

---

### Audit / Judge

**Audit**：Server 对索引集合 $`I`$ 计算聚合签名与非成员证明：

$$\nu = \sum_{i \in I} v_i \cdot s_i \in \mathbb{Z}_p, \quad \sigma_I = \prod_{i \in I} \sigma_i^{v_i} \in \mathbb{G}_1$$

其中 $`v_i \xleftarrow{R} \mathbb{Z}_p`$ 由 Client 选取，$`\pi_1 = \text{WitCreate}^\ast(\text{Acc}_R, R, Q_I)`$。

**Judge** 验证两个条件：

$$e(\sigma_I,\ g) = e\!\left(\prod_{i \in I} H_G(i \| \mathit{tag}_i)^{v_i} \cdot u^\nu,\ A\right)$$

$$\text{WitVerify}^\ast(\text{Acc}_R,\ R,\ Q_I,\ \pi_1) = 1$$

```python
# vads_lib.py:987  audit
nu += v_i * s_i
sigma_I *= sigma_i ** v_i
# judge：pair(sigma_I, g) == pair(Gamma * u**nu, A)
```

---

## 安全性

### 安全假设

| 假设 | 作用 |
|---|---|
| 强 RSA 假设（Strong RSA） | RSA 累加器不可伪造；攻击者无法构造满足验证等式的假证明，除非能对任意整数计算 $`n`$ 下的任意次方根 |
| $`q`$-SDH 假设 | BLS 签名不可伪造；攻击者无法在不知道 $`\alpha`$ 的情况下伪造满足配对等式的 $`\sigma_i`$ |
| 随机预言机模型（ROM） | $`H_{\text{prime}}`$（hash\_to\_prime）和 Fiat-Shamir 变换（NI-PoE 中的 $`l_1, l_2`$）的安全性归约依赖 |
| Type-3 双线性配对（BN254） | 聚合签名验证依赖 co-CDH 假设（$`\mathbb{G}_1 \times \mathbb{G}_2`$ 的计算 DH 问题困难） |

### 各操作的安全性论证

**Query / Verify 的不可伪造性**

假设攻击者伪造了针对 $`\mathit{tag}_i \in R`$ 的有效证明 $`(x, Y)`$，即找到满足

$$\text{Acc}_R^x \cdot Y^{z_i} \equiv h \pmod{n}$$

的 $`(x, Y)`$。由于 $`\text{Acc}_R = h^{z^\ast}`$，这等价于 $`h^{x z^\ast + y z_i} = h`$，即找到 $`z^\ast`$ 和 $`z_i`$ 满足此关系的整数解。因为 $`z_i \mid z^\ast`$（$`\mathit{tag}_i \in R`$），故 $`\gcd(z_i, z^\ast) = z_i > 1`$，Bezout 等式 $`x z^\ast + y z_i = 1`$ 无整数解，攻击者必须在 $`\mathbb{Z}_n^\ast`$ 中计算 $`h`$ 的 $`z_i`$ 次方根，由强 RSA 假设不可行。

**WitCreate\_star / WitVerify\_star 的安全性（NI-PoE）**

两层 NI-PoE 子证明（$`T_1, T_2`$）通过 Fiat-Shamir 变换将 BBF19 的交互式指数知识证明转为非交互式。在 ROM 下，$`l_1, l_2`$ 视为随机素数，攻击者无法预先选择使验证等式成立的 $`(T_1, T_2)`$，安全性归约至强 RSA 问题。

**Append / Audit 的不可伪造性**

BLS 签名满足 $`\sigma_i = (H_G(i \| \mathit{tag}_i) \cdot u^{s_i})^\alpha`$，伪造合法签名在 $`q`$-SDH 假设下不可行。Audit 使用随机挑战 $`v_i`$ 的线性组合，Judge 的配对等式验证聚合签名，不可伪造性规约至 BLS 聚合签名安全性。

**数据条数不影响安全性**

安全假设均为计算困难性假设，与数据条数 $`|DB|`$ 和撤销集合大小 $`|R|`$ 无关。tag 碰撞概率为 $`\binom{|DB|}{2} / 2^\lambda`$，在 $`\lambda = 128`$ 下即使 $`|DB| = 2^{64}`$ 碰撞概率仍约 $`2^{-1}`$，实际场景（$`|DB| \leq 2^{20}`$）可忽略不计。$`|R|`$ 增大仅影响验证性能（Bezout 系数位数线性增长），不削弱安全归约。

## 复现工作与差异

### RSA-accumulator 使用情况

`RSA-accumulator/` 目录保留自 [oleiba/RSA-accumulator](https://github.com/oleiba/RSA-accumulator) 原仓库代码，**未做修改**，但本项目仅使用其中两部分：

- `main.py:setup()`：生成 RSA 模数 `n` 和初始累加器值 `A0`
- `helpfunctions.py`：`hash_to_prime`、`mul_inv`、`concat` 等底层原语

原仓库提供的 `add / delete / prove_membership / verify_membership / prove_non_membership / batch_*` 等高层接口**均未调用**，原因如下：

- `prove/verify_non_membership`：接口每次调用需遍历整个集合 S 计算素数积（O(|S|)）；ovds 通过增量维护 `z_star = ∏HPrime(tag_j)` 将单查询证明生成降至 O(1)，故内联重实现而非复用
- `prove/verify_membership` 及 `batch_prove_membership_*`：方向不符——ovds 需要证明 tag **不在**撤销集合 R 中（非成员），而上述函数证明元素**在**集合中（成员），语义相反
- `add / delete`：ovds 不对累加器逐元素增删，直接用 `Acc_R = h^z_star mod n` 一步重算；R 集合只增不减，不需要 `delete`
- `batch_delete_using_membership_proofs`：依赖 Shamir trick 聚合成员证明，与 ovds 的聚合非成员证明（WitCreate_star）是不同问题，无法复用
- `create_all_membership_witnesses / aggregate_membership_witnesses`：同上，基于成员证明聚合，与 ovds 需求不符

### 本项目自行实现的部分

`src/vads_lib.py` 在 RSA accumulator 原语之上重新实现了以下内容：

**与原仓库等价的操作（独立实现，未复用原仓库函数）：**

- 单查询非成员证明（`query` 生成 `π=(x,Y)`）：等价于原仓库 `prove_non_membership`，利用 EEA(z\*, z_i) 求 Bezout 系数，数学结构相同，变量命名不同
- 单查询验证（`verify` 检查 `Acc_R^x · Y^z_i = h`）：等价于原仓库 `verify_non_membership`，同一等式的左右项顺序调换
- 累加器状态维护（`Acc_R = h^z_star mod n`）：等价于原仓库对集合 R 逐步执行 `add` 的最终结果，通过增量维护 `z_star = ∏HPrime(tag_j)` 实现常数级更新

**原仓库没有的扩展（论文 Algorithm 2）：**

- `WitCreate_star / WitVerify_star`：聚合非成员证明，支持一次证明多个 tag 均不在撤销集合 R 中；在 Bezout 系数基础上叠加两层 NI-PoE 子证明（T₁/T₂），避免暴露原始系数，原仓库无对应实现

**与 RSA accumulator 无关的部分：**

- `append / verify`：BLS 签名生成与配对验证，基于 charm-crypto，与 RSA accumulator 独立
- `audit / judge`：聚合签名审计协议
- `update`：数据更新时将旧 tag 纳入撤销集合并刷新 `Acc_R`

## 环境要求

- **必须在 WSL（Linux）下运行**，不支持 Windows 原生 Python
- Python 3.10+
- `charm-crypto` 依赖 PBC 库，仅支持 Linux

## 依赖安装

### 1. 安装系统库

```bash
sudo apt-get update
sudo apt-get install -y libpbc-dev libgmp-dev python3-dev python3-venv build-essential
```

### 2. 创建虚拟环境

```bash
python3 -m venv ~/crypto-libs-venv
source ~/crypto-libs-venv/bin/activate
```

### 3. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

> `charm-crypto` 若通过 pip 安装失败，需从源码编译：
> ```bash
> git clone https://github.com/JHUISI/charm.git
> cd charm
> ./configure.sh && make && pip install .
> ```

### 4. 激活环境（每次使用前）

```bash
source activate_venv.sh
```

脚本会自动探测 PBC 库路径。如需手动指定：

```bash
export LIB_PATH=/path/to/libpbc/lib   # PBC 库目录
export VENV_PATH=/path/to/venv        # 虚拟环境目录（非默认时）
source activate_venv.sh
```

## 运行

```bash
# 激活环境后
python -m unittest discover -s src/test   # 单元测试
python src/main.py                         # 完整性能基准（2^0 ~ 2^15）
```

Charm-Crypto 需要按其官方说明从源码安装；RSA 累加器的 Node.js 基准测试在 `RSA-accumulator/` 中单独运行。

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

## 安全假设与系统容量

### 安全假设

| 假设 | 作用 |
|---|---|
| 强 RSA 假设（Strong RSA）| RSA 累加器安全性基础；保证 Acc_R 不可伪造、非成员证明不可伪造 |
| q-SDH 假设（q-Strong Diffie-Hellman）| BLS 签名安全性基础；保证签名不可伪造 |
| 随机预言机模型（ROM）| hash_to_prime、Fiat-Shamir（NI-PoE）的安全归约依赖 |
| Type-3 双线性配对（BN254）| 聚合签名验证；依赖配对的计算 Diffie-Hellman 假设（co-CDH） |

### 存储开销

每条数据存储一条签名 σ_i（G1 群元素，BN254 下 32 字节）、一个标签 tag_i（128 bit = 16 字节）和数据值本身，服务端单条记录约 **48 字节 + 数据大小**。

累加器状态仅需维护：Acc_R（一个 3072 bit 整数，384 字节）和 z_star（一个整数，随更新次数增长，约 `128 × |R|` bit）。客户端只需保存 vk（常数大小）。

### 数据条数上限

协议本身对存储条数无硬性上限，实际受限于：

- RSA 模数规模：本实现固定使用 3072 bit 模数（128 bit 安全），每个 tag 哈希到 128 bit 素数；理论上可累积任意多条数据，但 `z_star` 的比特数随 `|R|` 线性增长
- 非成员证明中 Bezout 系数 x 的大小随 `|R|` 增大（约 `128 × |R|` bit），验证时的模幂运算开销相应增加

### 更新（R 集合）上限

R 集合大小直接影响：

- `z_star` 的位数：每次 update 追加一个 128 bit 素数，`|R|` 次更新后 z_star 约为 `128 × |R|` bit
- 单查询证明生成仍为 O(1)（依赖缓存 z_star），但验证时的 `Y^z_i mod n` 和 `Acc_R^x mod n` 中指数 x 的大小与 `|R|` 正相关，模幂耗时随之增长
- 本实现中 `sys.set_int_max_str_digits(100000)` 仅限制大整数与字符串的互转（print / json.dump），不影响 `pow` 与乘法，故不构成容量上限；100000 位十进制 ≈ 332000 bit ≈ 2593 次更新后的 z_star 规模，超出后序列化会报错，需调高该参数

协议无硬编码更新次数上限，大规模场景下建议定期对 R 集合做快照压缩（论文未覆盖，需工程扩展）。

## 一些思考

### 1. z\* 的素数碰撞

**问题**：每次 update 向 $`z^\ast`$ 追加一个 128 bit 素数，新素数会不会与 $`z^\ast`$ 中已有的相同？

- $`z^\ast`$ 本身不会重复：`update_z_star` 只做乘法不取模，$`z^\ast`$ 严格单调递增，重复概率为 0。
- 真正的风险是 $`H_{\text{prime}}`$ 输出碰撞。128 bit 素数空间 $`\pi(2^{128}) \approx 2^{128}/(128\ln 2) \approx 2^{121.5}`$，单次 update 碰撞概率 $`\approx |R| / 2^{121.5}`$，累计 $`\approx |R|^2 / 2^{122.5}`$。$`|R| = 2^{32}`$ 时累计约 $`2^{-58.5}`$，需约 $`2^{61}`$ 次更新才接近 1。
- 素数空间比 128 bit tag 空间小约 90 倍，瓶颈在素数映射而非 tag 长度，单纯加长 tag 无益。

**后果**（若发生）：$`z_i \mid z^\ast`$，`EEA` 返回 $`(0, 1)`$，`verify` 计算 $`h^{z_i} \not\equiv h`$ → 合法数据被永久拒绝；`query_star` 中整批 $`k`$ 条一起失败；`judge` 会错误指控诚实服务器；客户端无法区分碰撞与作恶。

**但不破坏可靠性（soundness）**：设 $`z^\ast = z_i \cdot m`$，伪造需 $`Y^{z_i} = h^{1 - x z_i m}`$，即要求 $`z_i \mid 1`$，对 $`z_i > 1`$ 恒不成立，攻击者只能在 $`\mathbb{Z}_n^\ast`$ 中开 $`z_i`$ 次方根 → 归约到强 RSA。**碰撞是可用性失效，不是安全性失效。**

另一种"碰撞"是 $`\text{Acc}_R`$ 取值重复，要求 $`z_1^\ast \equiv z_2^\ast \pmod{\text{ord}(h)}`$；能找到它就等于破解强 RSA，已被安全假设覆盖，无需单独防御。

### 2. `EEA` 丢弃了 gcd

`vads_lib.py:109` 的 `EEA` 文档声明返回满足 $`ax + by = \gcd(a,b)`$ 的系数，但实际只返回 $`(x, y)`$ 而丢弃 gcd；`query`（:627）与 `WitCreate_star`（:167）都未校验 $`\gcd = 1`$。建议二选一加固：

- **低成本**：`EEA` 额外返回 gcd，调用处在 $`\gcd \neq 1`$ 时抛出可区分的异常，避免把碰撞误判为服务器作恶。
- **防患于未然**：`update` 生成新 tag 时校验 `z_star % z_new != 0`，否则重抽 tag（代价是每次 update 一次 $`O(|z^\ast|)`$ 取模）。

### 3. 上游 `batch_delete` 的缺陷

`RSA-accumulator/main.py:171` 的 `batch_delete` 把被删除的 `x_list` 又传回 `batch_add`，相当于把删掉的元素重新加回累加器，正确做法应传剩余集合。`test.py` 只覆盖了 `batch_delete_using_membership_proofs`，未测到该函数。本项目未调用它，且该目录声明保持原仓库原样，故未修改。

### 4. R 只增不减的长期开销

撤销集合 R 单调增长，Bezout 系数 $`x`$ 的位数约 $`128 \times |R|`$ bit，`pow(Acc_R, x, n)` 的耗时随 $`|R|`$ 线性增长——证明生成因缓存 $`z^\ast`$ 仍是 O(1)，**但验证端不是**。论文未讨论 R 的压缩或换代机制，工程上需要定期快照（重新 Setup 并迁移未撤销数据）或采用分片累加器。

### 5. `set_int_max_str_digits` 的实际作用

`src/main.py:10`（10000）与 `vads_lib.py:16`（100000）设置了不同上限，且该参数只限制 int↔str 转换，不影响 `pow` 与乘法，因此它不是协议容量上限，只会在打印或 `json.dump` 序列化 $`z^\ast`$ 时抛错。真正的瓶颈是上面第 4 点的验证性能。
