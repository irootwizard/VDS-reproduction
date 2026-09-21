"""
VADS (Verifiable Data Streaming) 实现
基于 BLS 签名和 RSA Accumulator
使用 BN254 椭圆曲线和 3072 位 RSA 模数

根据算法图实现完整的 VADS 协议
"""

import secrets
import hashlib
import sys
import os

# 增加整数字符串转换限制，避免大数据集时audit操作报错
# 设置为更大的值以处理大审计集时的大整数转换
sys.set_int_max_str_digits(100000)

# 添加 RSA-accumulator 路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'RSA-accumulator'))

from helpfunctions import hash_to_prime, bezoute_coefficients, mul_inv, calculate_product, concat
from main import setup as accumulator_setup

# 尝试导入 charm 库
try:
    from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair
    CHARM_AVAILABLE = True
except ImportError as e:
    CHARM_AVAILABLE = False
    import sys
    print("警告: charm 库未安装，BLS 相关功能将无法使用")
    print(f"  Python 路径: {sys.executable}")
    print(f"  Python 版本: {sys.version.split()[0]}")
    print(f"  导入错误: {e}")
    print("  请安装: pip install charm-crypto")
    print("  或在虚拟环境中安装: source activate_venv.sh && pip install charm-crypto")

# RSA Accumulator 参数
RSA_KEY_SIZE = 3072  # 3072 bits RSA module for 128 bits security
RSA_PRIME_SIZE = int(RSA_KEY_SIZE / 2)
ACCUMULATED_PRIME_SIZE = 128  # 128 bits security

# 安全参数
SECURITY_PARAM = 128  # λ = 128 bits

# 全局变量（在 setup 函数中初始化）
_vk = None  # 验证密钥
_server_state = None  # 服务器状态


# ==================== 辅助函数 ====================

def H_G(x, group):
    """哈希函数 HG: {0,1}* -> G1"""
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    h = hashlib.sha256(str(x).encode()).digest()
    # 将哈希值映射到 G1 群（椭圆曲线 BN254 上的点）
    return group.hash(h, G1)  # 返回 G1 群元素（椭圆曲线点）


def H_G_2(x, group):
    """哈希函数 HG': {0,1}* -> G' (已废弃，保留用于兼容性)"""
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    h = hashlib.sha256(str(x).encode()).digest()
    return group.hash(h, G2)


def H_G_prime(x, n):
    """
    哈希函数 HG': {0,1}* -> G'
    G' 是 RSA accumulator 的群（模 n 的乘法群 Z_n*）
    返回一个整数（素数），用于 RSA 模运算
    """
    prime, _ = hash_to_prime(x, ACCUMULATED_PRIME_SIZE)
    return prime


def H_Primes(*args):
    """
    哈希函数 HPrimes: {0,1}* -> Primes(λ)
    返回一个素数，用于算法中的 l_1, l_2 等
    """
    # 将所有参数连接后哈希到素数
    combined = concat(*args)
    prime, _ = hash_to_prime(combined, ACCUMULATED_PRIME_SIZE)
    return prime


def H_2(x):
    """
    哈希函数 H2 (Hλ): {0,1}* -> [0, 2^λ)
    返回一个整数，用于算法中的 γ 等
    """
    h = hashlib.sha256(str(x).encode()).digest()
    return int.from_bytes(h[:SECURITY_PARAM // 8], 'big')


def H_prime(tag):
    """哈希函数 HPrime: {0,1}^λ -> Z_p (用于 RSA accumulator)"""
    # 将 tag 转换为素数（用于 RSA accumulator）
    prime, nonce = hash_to_prime(tag, ACCUMULATED_PRIME_SIZE)
    return prime


def EEA(a, b):
    """扩展欧几里得算法，返回 (x, y) 使得 a*x + b*y = gcd(a, b)"""
    x0, x1, y0, y1 = 1, 0, 0, 1
    while b != 0:
        q, a, b = a // b, b, a % b
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
    return x0, y0


def update_z_star(server_state, tag, n):
    """
    更新缓存的 z_star 值（常数级复杂度）
    当有新的 tag 添加到 R 集合时调用此函数
    
    Args:
        server_state: 服务器状态
        tag: 要添加到 R 的 tag
        n: RSA 模数
    """
    z_j = H_prime(tag)
    server_state['z_star'] = server_state['z_star'] * z_j


# ==================== Algorithm 2: RSA Accumulator 聚合非成员证明 ====================

def WitCreate_star(Acc_R, R, Q, n, h=None, z_star=None):
    """
    Algorithm 2: 创建聚合非成员证明
    Args:
        Acc_R: RSA accumulator 值（当前值，删除R后的值）
        R: 已删除的 tag 集合
        Q: 要证明非成员的 tag 集合（素数列表）
        n: RSA 模数
        h: 初始 accumulator 值（如果为None，使用Acc_R）
        z_star: 缓存的 z* 值（如果为None，则计算）
    Returns:
        π: 证明 {V, Y, T_1, T_2, X', r}
    """
    # 如果没有提供初始值，使用当前值（简化处理）
    if h is None:
        h = Acc_R
    
    # Step 1-2: 计算 z* = ∏_{tag_j ∈ R} HPrime(tag_j)
    # 如果提供了缓存的 z_star，直接使用；否则计算
    if z_star is None:
        z_star = 1
        for tag_j in R:
            z_j = H_prime(tag_j)
            z_star = z_star * z_j
    
    # Step 3: 计算 ω' = ∏_{z_i ∈ Q} z_i
    omega_prime = 1
    for z_i in Q:
        omega_prime = omega_prime * z_i
    
    # Step 4: 使用扩展欧几里得算法计算 (x, y) 使得 x*z* + y*ω' = 1
    # 注意：算法中是 EEA(z*, w')，所以应该是 EEA(z_star, omega_prime)
    x, y = EEA(z_star, omega_prime)
    
    # Step 5: 计算 V = (Acc_R)^x mod n
    if x < 0:
        positive_x = -x
        inv_Acc_R = mul_inv(Acc_R, n)
        V = pow(inv_Acc_R, positive_x, n)
    else:
        V = pow(Acc_R, x, n)
    
    # Step 6: 计算 Y = h^y mod n
    if y < 0:
        positive_y = -y
        inv_h = mul_inv(h, n)
        Y = pow(inv_h, positive_y, n)
    else:
        Y = pow(h, y, n)
    
    # Step 7: 计算 l_1 = HPrimes(ω', Y, h · V⁻¹)
    inv_V = mul_inv(V, n)
    h_V_inv = (h * inv_V) % n
    l_1 = H_Primes(omega_prime, Y, h_V_inv)
    
    # Step 8: 计算 t_1 = ⌊ω'/l_1⌋
    t_1 = omega_prime // l_1
    
    # Step 9: 计算 T_1 = Y^t_1 mod n
    T_1 = pow(Y, t_1, n) if t_1 > 0 else 1
    
    # Step 10: 计算 h' = HG'(Acc(R), V)
    # HG' 返回一个整数（素数），用于 RSA 模运算
    h_prime = H_G_prime(concat(Acc_R, V), n)
    
    # Step 11: 计算 X' = (h')^x mod n
    if x < 0:
        positive_x = -x
        inv_h_prime = mul_inv(h_prime, n)
        X_prime = pow(inv_h_prime, positive_x, n)
    else:
        X_prime = pow(h_prime, x, n)
    
    # Step 12: 计算 l_2 = HPrimes(Acc(R), V, X')
    l_2 = H_Primes(Acc_R, V, X_prime)
    
    # Step 13: 计算 γ = Hλ(Acc(R), V, X', l_2)
    gamma_input = concat(Acc_R, V, X_prime, l_2)
    gamma = H_2(gamma_input)
    
    # Step 14: 计算 t_2 = ⌊x/l_2⌋
    if x < 0:
        positive_x = -x
        t_2 = positive_x // l_2
    else:
        t_2 = x // l_2
    
    # Step 15: 计算 r = x mod l_2
    if x < 0:
        # 对于负数，需要特殊处理
        r = x % l_2
        if r < 0:
            r += l_2
    else:
        r = x % l_2
    
    # Step 16: 计算 T_2 = (Acc(R) · (h')^γ)^t_2 mod n
    h_prime_gamma = pow(h_prime, gamma, n)
    Acc_R_h_prime_gamma = (Acc_R * h_prime_gamma) % n
    if t_2 < 0:
        positive_t_2 = -t_2
        inv_Acc_R_h_prime_gamma = mul_inv(Acc_R_h_prime_gamma, n)
        T_2 = pow(inv_Acc_R_h_prime_gamma, positive_t_2, n)
    else:
        T_2 = pow(Acc_R_h_prime_gamma, t_2, n)
    
    # 返回证明
    pi = {
        'V': V,
        'Y': Y,
        'T_1': T_1,
        'T_2': T_2,
        'X_prime': X_prime,
        'r': r
    }
    
    return pi


def WitVerify_star(Acc_R, R, Q, pi, n, h=None):
    """
    Algorithm 2: 验证聚合非成员证明
    Args:
        Acc_R: RSA accumulator 值（当前值，删除R后的值）
        R: 已删除的 tag 集合
        Q: 要证明非成员的 tag 集合（素数列表）
        n: RSA 模数
        π: 证明
        h: 初始 accumulator 值（如果为None，使用Acc_R）
    Returns:
        1 如果验证通过，0 否则
    """
    # 如果没有提供初始值，使用当前值（简化处理）
    if h is None:
        h = Acc_R
    
    # Step 1: 从 π 提取组件
    V = pi['V']
    Y = pi['Y']
    T_1 = pi['T_1']
    T_2 = pi['T_2']
    X_prime = pi['X_prime']
    r = pi['r']
    
    # Step 2: 计算 ω' = ∏_{z_i ∈ Q} z_i
    omega_prime = 1
    for z_i in Q:
        omega_prime = omega_prime * z_i
    
    # Step 3: 计算 l_1 = HPrimes(ω', Y, h · Y⁻¹)
    inv_V = mul_inv(V, n)
    h_V_inv = (h * inv_V) % n
    l_1 = H_Primes(omega_prime, Y, h_V_inv)
    
    # Step 4: 计算 r' = ω' mod l_1
    r_prime = omega_prime % l_1
    
    # Step 5: 验证第一个条件: T_1^l_1 · Y^r' == h · V^-1 (mod n)
    left1 = (pow(T_1, l_1, n) * pow(Y, r_prime, n)) % n
    inv_V = mul_inv(V, n)
    right1 = (h * inv_V) % n
    
    if left1 != right1:
        return 0
    
    # Step 6: 计算 h' = HG'(Acc(R), V)
    # HG' 返回一个整数（素数），用于 RSA 模运算
    h_prime = H_G_prime(concat(Acc_R, V), n)
    
    # Step 7: 计算 l_2 = HPrimes(Acc(R), V, X')
    l_2 = H_Primes(Acc_R, V, X_prime)
    
    # Step 8: 计算 γ = Hλ(Acc(R), V, X', l_2)
    gamma_input = concat(Acc_R, V, X_prime, l_2)
    gamma = H_2(gamma_input)
    
    # Step 9: 验证第二个条件: T_2^l_2 · (Acc(R) · (h')^γ)^r == V · (X')^γ (mod n)
    h_prime_gamma = pow(h_prime, gamma, n)
    Acc_R_h_prime_gamma = (Acc_R * h_prime_gamma) % n
    left2 = (pow(T_2, l_2, n) * pow(Acc_R_h_prime_gamma, r, n)) % n
    
    X_prime_gamma = pow(X_prime, gamma, n)
    right2 = (V * X_prime_gamma) % n
    
    if left2 != right2:
        return 0
    
    # Step 11: 验证通过
    return 1


# ==================== Algorithm 1: VADS 主协议 ====================

def setup(security_param=SECURITY_PARAM):
    """
    Algorithm 1: Setup(1^λ)
    初始化 VADS 系统（使用 BN254 Type 3 非对称配对）
    
    Client 端:
    - 生成双线性配对群参数 (G, GT, e, p, g) 使用 BN254 曲线
    - 生成 g ∈ G2, A = g^α ∈ G2（公钥）
    - 生成 u ∈ G1
    - 生成 α ∈ Z_p (秘密值)
    - 初始化哈希函数 HG, HG', H2, HPrime
    - 初始化计数器 cnt = 0
    - 初始化 RSA Accumulator Acc(0)
    - 构造验证密钥 vk
    - 构造秘密密钥 sk = {α, cnt, vk}
    
    Server 端:
    - 存储 vk
    - 初始化 R = ∅ (已删除的 tag 集合)
    - 初始化 DB = ∅ (数据库)
    
    Returns:
        (vk, sk, server_state): 
            vk: 验证密钥
            sk: 秘密密钥
            server_state: 服务器状态 {'vk': vk, 'R': set(), 'DB': {}, 'Acc_R': Acc_0}
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装，无法初始化双线性配对群")
    
    # Client 端操作
    # Step 1-2: 初始化双线性配对群 (G, GT, e, p, g) 使用 BN254 曲线（Type 3 非对称配对）
    group = PairingGroup('BN254')
    G = group
    GT = group
    g = group.random(G2)  # 生成元 g ∈ G2
    
    # Step 3: 初始化 RSA Accumulator
    n, A0, S = accumulator_setup()
    Acc_0 = A0
    
    # Step 4: 生成 G'（RSA accumulator 的群，即模 n 的乘法群 Z_n*）
    G_prime = n
    
    # Step 5: 生成 u ∈ G1
    u = group.random(G1)
    
    # Step 6: 生成 α ∈ Z_p (秘密值)
    alpha = group.random(ZR)
    
    # Step 7: 计算 A = g^α
    A = g ** alpha  # A ∈ G2（公钥）
    
    # Step 8-11: 初始化哈希函数 (HG, HG', H2, HPrime 已在上面定义)
    
    # Step 12: 初始化计数器
    cnt = 0
    
    # Step 13: 构造验证密钥 vk
    # 注意：h 应该是 RSA accumulator 初始值（整数），即 Acc(∅) = Acc_0
    # 根据算法：Acc(∅) ← h，所以 h = Acc_0
    vk = {
        'group': group,
        'G': G,
        'GT': GT,
        'g': g,
        'G_prime': G_prime,  # RSA accumulator 的群（由模数 n 定义）
        'h': Acc_0,  # RSA accumulator 初始值（整数，mod n），即 Acc(∅)
        'u': u,
        'A': A,
        'n': n,  # RSA 模数
        'Acc_0': Acc_0,  # 初始 RSA accumulator 值
        'HG': lambda x: H_G(x, group),
        'HG_prime': lambda x: H_G_prime(x, n),  # 修正：使用返回整数的 H_G_prime
        'H2': H_2,
        'HPrime': H_prime
    }
    
    # Step 14: 构造秘密密钥 sk
    sk = {
        'alpha': alpha,
        'cnt': cnt,
        'vk': vk
    }
    
    # Server 端操作
    # Step 15-16: 初始化服务器状态
    server_state = {
        'vk': vk,
        'R': set(),  # 已删除的 tag 集合
        'DB': {},    # 数据库: {i: (s[i], σ_i, tag_i)}（索引 i 作为字典 key）
        'Acc_R': Acc_0,  # 当前 RSA accumulator 值
        'z_star': 1  # 缓存的 z* = ∏_{tag_j ∈ R} HPrime(tag_j) mod n
    }
    
    return vk, sk, server_state


def append(sk, s, server_state):
    """
    Algorithm 1: Append(sk, s, DB)
    添加数据项到数据库
    
    Client 端:
    - 提取 sk 组件
    - 设置索引 i = cnt
    - 生成 tag_i ∈ {0,1}^λ
    - 计算 σ_i = (HG(i||tag_i) * u^s)^α
    - 递增 cnt
    - 返回 (i, s, σ_i, tag_i)
    
    Server 端:
    - 验证 e(σ_i, g) == e(HG(i||tag_i) * u^s, A)（e: G1 × G2 → GT）
    - 如果验证通过，存储 (s, σ_i, tag_i) 到 DB[i]（索引 i 作为字典 key）
    - 否则返回 ⊥
    
    Args:
        sk: 秘密密钥
        s: 要添加的数据项（整数）
        server_state: 服务器状态
    
    Returns:
        (i, s, σ_i, tag_i): 添加的数据项和签名
        如果验证失败返回 None
    """
    # Client 端操作
    # Step 1: 提取 sk 组件
    alpha = sk['alpha']
    cnt = sk['cnt']
    vk = sk['vk']
    group = vk['group']
    g = vk['g']
    u = vk['u']
    A = vk['A']
    HG = vk['HG']

    # Step 2: 设置索引 i = cnt
    i = cnt

    # Step 3: 生成 tag_i ∈ {0,1}^λ
    tag_i = secrets.randbits(SECURITY_PARAM)

    # Step 4: 计算 BLS 签名 σ_i = (HG(i||tag_i) * u^s)^α
    i_tag_concat = str(i) + str(tag_i)
    HG_i_tag = HG(i_tag_concat)  # HG: {0,1}* -> G1
    u_s = u ** s  # u^s ∈ G1
    HG_i_tag_u_s = HG_i_tag * u_s  # G1 群点加法
    sigma_i = HG_i_tag_u_s ** alpha  # σ_i ∈ G1（BLS 签名）

    # Step 5: 递增计数器
    sk['cnt'] = cnt + 1

    # Server 端操作
    # Step 6: 验证签名 e(σ_i, g) == e(HG(i||tag_i) * u^s, A)
    e_sigma_g = pair(sigma_i, g)  # e(G1, G2) → GT
    e_A_HG_u = pair(HG_i_tag * u_s, A)  # e(G1, G2) → GT
    if e_sigma_g != e_A_HG_u:
        return None
    
    # Step 7: 存储 (s, σ_i, tag_i) 到 DB[i]（索引 i 作为字典 key，不需要存储在元组中）
    server_state['DB'][i] = (s, sigma_i, tag_i)
    
    return (i, s, sigma_i, tag_i)

def append_client(sk, s):
    """
    Append 的 Client 端操作
    生成签名和参数
    
    Client 端:
    - 提取 sk 组件
    - 设置索引 i = cnt
    - 生成 tag_i ∈ {0,1}^λ
    - 计算 σ_i = (HG(i||tag_i) * u^s)^α
    - 递增 cnt
    - 返回 (i, s, σ_i, tag_i)
    
    Args:
        sk: 秘密密钥
        s: 要添加的数据项（整数）
    
    Returns:
        (i, s, σ_i, tag_i): 索引、数据项、签名和标签
    """
    # Step 1: 提取 sk 组件
    alpha = sk['alpha']
    cnt = sk['cnt']
    vk = sk['vk']
    group = vk['group']
    u = vk['u']
    HG = vk['HG']

    # Step 2: 设置索引 i = cnt
    i = cnt

    # Step 3: 生成 tag_i ∈ {0,1}^λ
    tag_i = secrets.randbits(SECURITY_PARAM)

    # Step 4: 计算 BLS 签名 σ_i = (HG(i||tag_i) * u^s)^α
    i_tag_concat = str(i) + str(tag_i)
    HG_i_tag = HG(i_tag_concat)  # HG: {0,1}* -> G1
    u_s = u ** s  # u^s ∈ G1
    HG_i_tag_u_s = HG_i_tag * u_s  # G1 群点加法
    sigma_i = HG_i_tag_u_s ** alpha  # σ_i ∈ G1（BLS 签名）

    # Step 5: 递增计数器
    sk['cnt'] = cnt + 1
    
    return (i, s, sigma_i, tag_i)


def append_server(vk, server_state, i, s, sigma_i, tag_i):
    """
    Append 的 Server 端操作
    验证签名并存储数据
    
    Server 端:
    - 验证 e(σ_i, g) == e(HG(i||tag_i) * u^s, A)（e: G1 × G2 → GT）
    - 如果验证通过，存储 (s, σ_i, tag_i) 到 DB[i]（索引 i 作为字典 key）
    - 否则返回 ⊥
    
    Args:
        vk: 验证密钥
        server_state: 服务器状态
        i: 数据项索引
        s: 数据项值
        sigma_i: BLS 签名
        tag_i: 标签
    
    Returns:
        (i, s, σ_i, tag_i): 如果验证成功
        None: 如果验证失败
    """
    # Step 1: 提取 vk 组件
    group = vk['group']
    g = vk['g']
    u = vk['u']
    A = vk['A']
    HG = vk['HG']
    
    # Step 2: 验证签名 e(σ_i, g) == e(HG(i||tag_i) * u^s, A)
    i_tag_concat = str(i) + str(tag_i)
    HG_i_tag = HG(i_tag_concat)  # HG: {0,1}* -> G1
    u_s = u ** s  # u^s ∈ G1
    HG_i_tag_u_s = HG_i_tag * u_s  # G1 群点加法
    
    e_sigma_g = pair(sigma_i, g)  # e(G1, G2) → GT
    e_A_HG_u = pair(HG_i_tag_u_s, A)  # e(G1, G2) → GT
    if e_sigma_g != e_A_HG_u:
        return None
    
    # Step 3: 存储 (s, σ_i, tag_i) 到 DB[i]（索引 i 作为字典 key，不需要存储在元组中）
    server_state['DB'][i] = (s, sigma_i, tag_i)
    
    return (i, s, sigma_i, tag_i)




def query(vk, server_state, i):
    """
    Algorithm 1: Query(vk, DB, i)
    单次查询数据项
    
    Server 端:
    - 从 DB[i] 检索 (s[i], σ_i, tag_i)
    - 计算 z_i = HPrime(tag_i)
    - 计算 z* = ∏_{tag_j ∈ R} HPrime(tag_j)
    - 使用 EEA(z*, z_i) 计算 (x, y)
    - 计算 Y = h^y mod n
    - 构造证明 π = (x, Y)
    - 构造 π_q = {σ_i, tag_i, π}
    - 返回 s[i] 和 π_q
    
    Args:
        vk: 验证密钥
        server_state: 服务器状态
        i: 数据项索引
    
    Returns:
        (s_i, π_q): 数据项和证明
        如果索引不存在，返回 None
    """
    # Server 端操作 
    # Step 1: 从 DB[i] 检索 (s[i], σ_i, tag_i)
    if i not in server_state['DB']:
        return None
    
    s_i, sigma_i, tag_i = server_state['DB'][i]

    # Step 2: 计算 z_i = HPrime(tag_i)
    HPrime = vk['HPrime']
    z_i = HPrime(tag_i)

    # Step 3: 使用缓存的 z* = ∏_{tag_j ∈ R} HPrime(tag_j) (常数级复杂度)
    n = vk['n']
    z_star = server_state['z_star']

    # Step 4: 使用 EEA(z*, z_i) 计算 (x, y)
    x, y = EEA(z_star, z_i)
    
    # Step 5: 计算 Y = h^y mod n 
    h = vk['h']  # RSA accumulator 初始值
    if y < 0:
        positive_y = -y
        inv_h = mul_inv(h, n)
        Y = pow(inv_h, positive_y, n)
    else:
        Y = pow(h, y, n)
    
    # Step 6: 构造证明 π = (x, Y)
    pi = {
        'x': x,
        'Y': Y
    }
    
    # Step 7: 构造 π_q = {σ_i, tag_i, π}
    pi_q = {
        'sigma_i': sigma_i,
        'tag_i': tag_i,
        'pi': pi
    }
    
    # Step 8: 返回 s[i] 和 π_q
    return (s_i, pi_q)


def query_star(vk, server_state, J):
    """
    Algorithm 1: Query*(vk, J, DB)
    并发查询多个数据项
    
    Server 端:
    - 初始化 Q_J
    - 对于每个 j ∈ J:
        - 从 DB[j] 检索 (s[j], σ_j, tag_j)
        - 更新 Q_J 添加 HPrime(tag_j)
    - 计算 π_J = WitCreate*(Acc(R), R, Q_J)
    - 构造 π_a = {{{j, σ_j, tag_j) | j ∈ J}, π_J}}
    - 返回 S[J] 和 π_q
    
    Args:
        vk: 验证密钥
        server_state: 服务器状态
        J: 数据项索引列表
    
    Returns:
        (S[J], π_q): 数据项列表和证明
        如果任何索引不存在，返回 None
    """
    # Server 端操作
    # Step 1: 初始化 Q_J（tag 的素数列表）
    Q_J = []
    S_J = []  # 数据项值列表
    items = []  # {(j, σ_j, tag_j) | j ∈ J}
    
    # Step 2: 对于每个 j ∈ J
    HPrime = vk['HPrime']
    for j in J:
        # Step 2.1: 从 DB[j] 检索 (s[j], σ_j, tag_j)
        if j not in server_state['DB']:
            return None  # 如果索引不存在，返回 None
        
        s_j, sigma_j, tag_j = server_state['DB'][j]
        
        # Step 2.2: 更新 Q_J 添加 HPrime(tag_j)
        z_j = HPrime(tag_j)
        Q_J.append(z_j)
        
        # Step 2.3: 更新 S_J 和 items
        S_J.append(s_j)
        items.append((j, sigma_j, tag_j))
    
    # Step 3: 计算 π_J = WitCreate_star(Acc(R), R, Q_J, n, h)
    Acc_R = server_state['Acc_R']
    R = server_state['R']
    n = vk['n']
    h = vk['h']  # RSA accumulator 初始值
    z_star = server_state['z_star']  # 使用缓存的 z_star（常数级复杂度）
    
    pi_J = WitCreate_star(Acc_R, R, Q_J, n, h, z_star)
    
    # Step 4: 构造 π_q = {{{j, σ_j, tag_j) | j ∈ J}, π_J}}
    pi_q = {
        'items': items,  # {(j, σ_j, tag_j) | j ∈ J}
        'pi_J': pi_J     # 聚合非成员证明
    }
    
    # Step 5: 返回 S[J] 和 π_q
    return (S_J, pi_q)


def verify(vk, s_i, i, pi_q, Acc_R=None):
    """
    Algorithm 1: Verify(vk, s[i], i, π_q)
    验证单次查询结果
    
    Client 端:
    - 检查 e(σ_i, g) == e(HG(i||tag_i) * u^s[i], A)（e: G1 × G2 → GT）
    - 如果失败返回 ⊥
    - 从 π_q 提取 σ_i, tag_i, π = (x, Y)
    - 计算 z_i = HPrime(tag_i)
    - 检查 (Acc(R))^x * Y^z_i = h
    - 如果失败返回 ⊥
    - 否则返回 s[i]
    
    Args:
        vk: 验证密钥
        s_i: 数据项值
        i: 数据项索引
        pi_q: 证明（应该包含 sigma_i, tag_i, pi）
        Acc_R: 当前的 RSA accumulator 值（如果为None，使用 vk['Acc_0']）
    
    Returns:
        s[i] 如果验证通过，None 否则
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    # Client 端操作
    # Step 1: 从 π_a 提取 σ_i, tag_i, π = (x, Y)
    if 'sigma_i' not in pi_q or 'tag_i' not in pi_q or 'pi' not in pi_q:
        return None
    
    sigma_i = pi_q['sigma_i']
    tag_i = pi_q['tag_i']
    pi = pi_q['pi']
    
    if 'x' not in pi or 'Y' not in pi:
        return None
    
    x = pi['x']
    Y = pi['Y']
    
    # Step 2: 提取验证密钥组件
    group = vk['group']
    g = vk['g']
    A = vk['A']
    u = vk['u']
    HG = vk['HG']
    HPrime = vk['HPrime']
    n = vk['n']
    h = vk['h']  # RSA accumulator 初始值
    
    # Step 3: 检查 BLS 签名 e(σ_i, g) == e(HG(i||tag_i) * u^s[i], A)
    i_tag_concat = str(i) + str(tag_i)
    HG_i_tag = HG(i_tag_concat)  # HG: {0,1}* -> G1
    u_s_i = u ** s_i  # u^s_i ∈ G1
    HG_i_tag_u_s = HG_i_tag * u_s_i  # G1 群点加法
    
    e_sigma_g = pair(sigma_i, g)  # e(G1, G2) → GT
    e_A_HG_u = pair(HG_i_tag_u_s, A)  # e(G1, G2) → GT
    
    if e_sigma_g != e_A_HG_u:
        return None  # 签名验证失败
    
    # Step 4: 计算 z_i = HPrime(tag_i)
    z_i = HPrime(tag_i)
    
    # Step 5: 获取当前的 Acc(R) 值
    if Acc_R is None:
        # 如果没有提供 Acc_R，使用初始值（这在实际应用中应该从服务器获取）
        Acc_R = vk['Acc_0']
    
    # Step 6: 检查 (Acc(R))^x * Y^z_i = h (mod n)
    # 注意：如果 x < 0，需要计算 Acc(R) 的逆元
    if x < 0:
        positive_x = -x
        inv_Acc_R = mul_inv(Acc_R, n)
        Acc_R_x = pow(inv_Acc_R, positive_x, n)
    else:
        Acc_R_x = pow(Acc_R, x, n)
    
    Y_z_i = pow(Y, z_i, n)
    left = (Acc_R_x * Y_z_i) % n
    right = h % n
    
    if left != right:
        return None  # RSA accumulator 非成员证明验证失败
    
    # Step 7: 验证通过，返回 s[i]
    return s_i


def verify_star(vk, S_J, J, pi_q, Acc_R=None, R=None):
    """
    Algorithm 1: Verify*(vk, S[J], J, π_a)
    验证并发查询结果
    
    Client 端:
    - 从 π_a 提取 {{(j, σ_j, tag_j) | j ∈ J}, π_J}
    - 计算 σ_J = ∏_{j ∈ J} σ_j
    - 计算 s' = Σ_{j ∈ J} s[j]
    - 检查 e(σ_J, g) == e(∏_{j ∈ J} HG(j||tag_j) * u^s', A)（e: G1 × G2 → GT）
    - 如果失败返回 ⊥
    - 计算 Q_J = {HPrime(tag_j) | j ∈ J}
    - 计算 b = WitVerify*(Acc(R), R, Q_J, π_J)
    - 检查 b == 1，如果失败返回 ⊥
    - 否则返回 S[J]
    
    Args:
        vk: 验证密钥
        S_J: 数据项值列表
        J: 数据项索引列表
        pi_q: 证明（应该包含 items 和 pi_J）
        Acc_R: 当前的 RSA accumulator 值（如果为None，使用 vk['Acc_0']）
        R: 已删除的 tag 集合（如果为None，使用空集合）
    
    Returns:
        S[J] 如果验证通过，None 否则
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    # Client 端操作
    # Step 1: 从 π_q 提取 {{(j, σ_j, tag_j) | j ∈ J}, π_J}
    if 'items' not in pi_q or 'pi_J' not in pi_q:
        return None
    
    items = pi_q['items']  # [(j, σ_j, tag_j) | j ∈ J]
    pi_J = pi_q['pi_J']    # 聚合非成员证明
    
    # 验证 items 和 J 的长度匹配
    if len(items) != len(J) or len(items) != len(S_J):
        return None
    
    # 验证索引匹配
    for idx, (j, sigma_j, tag_j) in enumerate(items):
        if j != J[idx]:
            return None
    
    # Step 2: 提取验证密钥组件
    group = vk['group']
    g = vk['g']
    A = vk['A']
    u = vk['u']
    HG = vk['HG']
    HPrime = vk['HPrime']
    n = vk['n']
    h = vk['h']  # RSA accumulator 初始值
    
    # Step 3: 计算 σ_J = ∏_{j ∈ J} σ_j（G1 群中聚合签名）
    sigma_J = group.init(G1, 1)  # G1 群单位元
    for j, sigma_j, tag_j in items:
        sigma_J = sigma_J * sigma_j  # G1 群点加法
    
    # Step 4: 计算 s' = Σ_{j ∈ J} s[j]
    s_prime = sum(S_J)
    
    # Step 5: 计算 ∏_{j ∈ J} HG(j||tag_j)（G1 群中聚合哈希值）
    HG_product = group.init(G1, 1)  # G1 群单位元
    for j, sigma_j, tag_j in items:
        j_tag_concat = str(j) + str(tag_j)
        HG_j_tag = HG(j_tag_concat)  # HG: {0,1}* -> G1
        HG_product = HG_product * HG_j_tag  # G1 群点加法
    
    # Step 6: 计算 u^s'
    u_s_prime = u ** s_prime  # u^s' ∈ G1
    
    # Step 7: 检查 BLS 聚合签名 e(σ_J, g) == e(∏_{j ∈ J} HG(j||tag_j) * u^s', A)
    HG_product_u_s = HG_product * u_s_prime  # G1 群点加法
    e_sigma_J_g = pair(sigma_J, g)  # e(G1, G2) → GT
    e_A_HG_u = pair(HG_product_u_s, A)  # e(G1, G2) → GT
    
    if e_sigma_J_g != e_A_HG_u:
        return None  # 聚合签名验证失败
    
    # Step 8: 计算 Q_J = {HPrime(tag_j) | j ∈ J}（素数列表）
    Q_J = []
    for j, sigma_j, tag_j in items:
        z_j = HPrime(tag_j)
        Q_J.append(z_j)
    
    # Step 9: 获取当前的 Acc(R) 和 R 值
    if Acc_R is None:
        # 如果没有提供 Acc_R，使用初始值（这在实际应用中应该从服务器获取）
        Acc_R = vk['Acc_0']
    
    if R is None:
        # 如果没有提供 R，使用空集合（这在实际应用中应该从服务器获取）
        R = set()
    
    # Step 10: 计算 b = WitVerify_star(Acc(R), R, Q_J, π_J, n, h)
    b = WitVerify_star(Acc_R, R, Q_J, pi_J, n, h)
    
    # Step 11: 检查 b == 1（验证通过），如果失败返回 None
    if b != 1:
        return None  # RSA accumulator 非成员证明验证失败
    
    # Step 12: 验证通过，返回 S[J]
    return S_J


def audit(vk, I, server_state):
    """
    Algorithm 1: Audit(vk, I, DB)
    数据审计
    
    Client 端:
    - 设置 I = [cnt] (所有索引)
    - 对于每个 i ∈ I，随机选择 v_i ∈ Z_p
    - 返回 {(i, v_i) | i ∈ I}
    
    Server 端:
    - 初始化 ν, σ_I, Q_I
    - 对于每个 i ∈ I:
        - 从 DB[i] 检索 (s[i], σ_i, tag_i)
        - 更新 ν += v_i * s[i]
        - 更新 σ_I *= σ_i^v_i
        - 更新 Q_I 添加 HPrime(tag_i)
    - 计算 π_1 = WitCreate*(Acc(R), R, Q_I)
    - 构造 π_a = {ν, σ_I, π_1, {tag_i | i ∈ I}}
    - 返回 π_a
    
    Args:
        vk: 验证密钥
        I: 审计索引集合（如果为None，则审计所有数据）
        server_state: 服务器状态
    
    Returns:
        π_a: 审计证明，包含 {ν, σ_I, π_1, tags, v_dict}，其中 v_dict = {(i, v_i) | i ∈ I}
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    # Step 1: 确定审计索引集合 I
    if I is None:
        # 如果 I 为 None，则审计所有数据
        I = sorted(server_state['DB'].keys())
    
    if len(I) == 0:
        return None  # 没有数据可审计
    
    # Step 2: Client 端 - 对于每个 i ∈ I，随机选择 v_i ∈ Z_p
    group = vk['group']
    v_dict = {}  # {(i, v_i) | i ∈ I}
    for i in I:
        v_i = group.random(ZR)  # 随机选择 v_i ∈ Z_p
        v_dict[i] = v_i
    
    # Step 3: Server 端 - 初始化 ν, σ_I, Q_I
    nu = group.init(ZR, 0)  # ν = 0（在 Z_p 中）
    sigma_I = group.init(G1, 1)  # σ_I = G1 单位元
    Q_I = []  # Q_I = []
    tags = {}  # {i: tag_i | i ∈ I}
    
    # Step 4: 提取验证密钥组件
    HPrime = vk['HPrime']
    
    # Step 5: 对于每个 i ∈ I
    for i in I:
        # Step 5.1: 从 DB[i] 检索 (s[i], σ_i, tag_i)
        if i not in server_state['DB']:
            return None  # 索引不存在
        
        s_i, sigma_i, tag_i = server_state['DB'][i]
        
        # Step 5.2: 更新 ν += v_i * s[i]
        v_i = v_dict[i]
        nu = nu + v_i * s_i  # ν += v_i * s[i]（在 Z_p 中）
        
        # Step 5.3: 更新 σ_I *= σ_i^v_i
        sigma_i_v_i = sigma_i ** v_i  # σ_i^v_i ∈ G1
        sigma_I = sigma_I * sigma_i_v_i  # σ_I *= σ_i^v_i（G1 群点加法）
        
        # Step 5.4: 更新 Q_I 添加 HPrime(tag_i)
        z_i = HPrime(tag_i)
        Q_I.append(z_i)
        
        # Step 5.5: 保存 tag_i
        tags[i] = tag_i
    
    # Step 6: 计算 π_1 = WitCreate_star(Acc(R), R, Q_I, n, h)
    Acc_R = server_state['Acc_R']
    R = server_state['R']
    n = vk['n']
    h = vk['h']  # RSA accumulator 初始值
    z_star = server_state['z_star']  # 使用缓存的 z_star（常数级复杂度）
    
    pi_1 = WitCreate_star(Acc_R, R, Q_I, n, h, z_star)
    
    # Step 7: 构造 π_a = {ν, σ_I, π_1, {tag_i | i ∈ I}, v_dict}
    pi_a = {
        'nu': nu,           # ν
        'sigma_I': sigma_I,  # σ_I
        'pi_1': pi_1,        # π_1
        'tags': tags,        # {i: tag_i | i ∈ I}
        'v_dict': v_dict,    # {(i, v_i) | i ∈ I}（用于 judge 函数）
        'I': I               # 索引列表（用于 judge 函数）
    }
    
    # Step 8: 返回 π_a
    return pi_a


def judge(vk, pi_a, Acc_R=None, R=None):
    """
    Algorithm 1: Judge(vk, π_a)
    审计评判
    
    Client 端:
    - 从 π_a 提取 {ν, σ_I, π_1, {tag_i | i ∈ I}}
    - 计算 Q_I = {HPrime(tag_i) | i ∈ I}
    - 计算 b = WitVerify*(Acc(R), R, Q_I, π_1)
    - 检查 b == 1，如果失败返回 0（注意：注释中写的是 b == 0，但应该是 b == 1，因为 WitVerify_star 返回 1 表示验证通过）
    - 计算 Γ = ∏_{i ∈ I} HG(i||tag_i)^v_i
    - 检查 e(σ_I, g) == e(Γ * u^ν, A)
    - 如果失败返回 0
    - 否则返回 1
    
    Args:
        vk: 验证密钥
        pi_a: 审计证明（应该包含 nu, sigma_I, pi_1, tags, v_dict, I）
        Acc_R: 当前的 RSA accumulator 值（如果为None，使用 vk['Acc_0']）
        R: 已删除的 tag 集合（如果为None，使用空集合）
    
    Returns:
        1 如果验证通过，0 否则
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    # Step 1: 从 π_a 提取 {ν, σ_I, π_1, {tag_i | i ∈ I}, v_dict, I}
    if 'nu' not in pi_a or 'sigma_I' not in pi_a or 'pi_1' not in pi_a or 'tags' not in pi_a or 'v_dict' not in pi_a or 'I' not in pi_a:
        return 0
    
    nu = pi_a['nu']           # ν
    sigma_I = pi_a['sigma_I'] # σ_I
    pi_1 = pi_a['pi_1']       # π_1
    tags = pi_a['tags']       # {i: tag_i | i ∈ I}
    v_dict = pi_a['v_dict']   # {(i, v_i) | i ∈ I}
    I = pi_a['I']             # 索引列表
    
    # Step 2: 提取验证密钥组件
    group = vk['group']
    g = vk['g']
    A = vk['A']
    u = vk['u']
    HG = vk['HG']
    HPrime = vk['HPrime']
    n = vk['n']
    h = vk['h']  # RSA accumulator 初始值
    
    # Step 3: 计算 Q_I = {HPrime(tag_i) | i ∈ I}
    Q_I = []
    for i in I:
        if i not in tags:
            return 0  # tag_i 不存在
        tag_i = tags[i]
        z_i = HPrime(tag_i)
        Q_I.append(z_i)
    
    # Step 4: 获取当前的 Acc(R) 和 R 值
    if Acc_R is None:
        # 如果没有提供 Acc_R，使用初始值（这在实际应用中应该从服务器获取）
        Acc_R = vk['Acc_0']
    
    if R is None:
        # 如果没有提供 R，使用空集合（这在实际应用中应该从服务器获取）
        R = set()
    
    # Step 5: 计算 b = WitVerify_star(Acc(R), R, Q_I, π_1, n, h)
    b = WitVerify_star(Acc_R, R, Q_I, pi_1, n, h)
    
    # Step 6: 检查 b == 1（验证通过），如果失败返回 0
    # 注意：注释中写的是 b == 0，但应该是 b == 1，因为 WitVerify_star 返回 1 表示验证通过
    if b != 1:
        return 0
    
    # Step 7: 计算 Γ = ∏_{i ∈ I} HG(i||tag_i)^v_i
    Gamma = group.init(G1, 1)  # Γ = G1 单位元
    for i in I:
        if i not in tags or i not in v_dict:
            return 0  # tag_i 或 v_i 不存在
        
        tag_i = tags[i]
        v_i = v_dict[i]
        
        # 计算 HG(i||tag_i)
        i_tag_concat = str(i) + str(tag_i)
        HG_i_tag = HG(i_tag_concat)  # HG: {0,1}* -> G1
        
        # 计算 HG(i||tag_i)^v_i
        HG_i_tag_v_i = HG_i_tag ** v_i  # HG(i||tag_i)^v_i ∈ G1
        
        # 更新 Γ *= HG(i||tag_i)^v_i
        Gamma = Gamma * HG_i_tag_v_i  # G1 群点加法
    
    # Step 8: 计算 u^ν
    u_nu = u ** nu  # u^ν ∈ G1
    
    # Step 9: 计算 Γ * u^ν
    Gamma_u_nu = Gamma * u_nu  # G1 群点加法
    
    # Step 10: 检查 e(σ_I, g) == e(Γ * u^ν, A)
    # 注意：根据 BLS 签名验证，应该是 e(σ_I, g) == e(Γ * u^ν, A)
    # 即 e(G1, G2) == e(G1, G2)
    e_sigma_I_g = pair(sigma_I, g)  # e(σ_I, g) → GT
    e_Gamma_u_nu_A = pair(Gamma_u_nu, A)  # e(Γ * u^ν, A) → GT
    
    if e_sigma_I_g != e_Gamma_u_nu_A:
        return 0  # 配对验证失败
    
    # Step 11: 验证通过，返回 1
    return 1


def update(sk, i, s_prime, vk, server_state):
    """
    Algorithm 1: Update(sk, i, s', vk, DB)
    更新数据项
    
    Client 端:
    - 从 DB[i] 检索 (s[i], σ_i, tag_i)
    - 检查 e(σ_i, g) == e(A, HG(i||tag_i) * u^s[i])
    - 如果失败返回 ⊥
    - 生成新的 tag_i' ∈ {0,1}^λ
    - 计算 σ_i' = (HG(i||tag_i') * u^s')^α
    - 更新 Acc(R) = Acc(R) * HPrime(tag_i) (将旧tag添加到删除集合)
    - 返回 (s', σ_i', tag_i')
    
    Server 端:
    - 检查 e(σ_i', g) == e(A, HG(i||tag_i') * u^s')
    - 如果失败返回 ⊥
    - 更新 DB[i] = (s', σ_i', tag_i')（索引 i 作为字典 key）
    - 更新 R = R ∪ {tag_i} (添加旧的 tag_i 到删除集合)
    - 调用 update_z_star(server_state, tag_i, n) 更新缓存的 z_star
    
    Args:
        sk: 秘密密钥
        i: 数据项索引
        s_prime: 新的数据项值
        vk: 验证密钥
        server_state: 服务器状态
    
    Returns:
        (s', σ_i', tag_i') 如果成功，None 否则
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    # Client 端操作
    # Step 1: 提取 sk 组件
    alpha = sk['alpha']
    group = vk['group']
    g = vk['g']
    u = vk['u']
    A = vk['A']
    HG = vk['HG']
    HPrime = vk['HPrime']
    n = vk['n']
    
    # Step 2: 从 DB[i] 检索 (s[i], σ_i, tag_i)
    if i not in server_state['DB']:
        return None  # 索引不存在
    
    s_i, sigma_i, tag_i = server_state['DB'][i]
    
    # Step 3: 检查 e(σ_i, g) == e(A, HG(i||tag_i) * u^s[i])
    i_tag_concat = str(i) + str(tag_i)
    HG_i_tag = HG(i_tag_concat)  # HG: {0,1}* -> G1
    u_s_i = u ** s_i  # u^s[i] ∈ G1
    HG_i_tag_u_s_i = HG_i_tag * u_s_i  # G1 群点加法
    
    e_sigma_g = pair(sigma_i, g)  # e(σ_i, g) ∈ GT
    e_A_HG_u = pair(HG_i_tag_u_s_i, A)  # e(HG(i||tag_i) * u^s[i], A) ∈ GT
    if e_sigma_g != e_A_HG_u:
        return None  # 验证失败，返回 ⊥
    
    # Step 4: 生成新的 tag_i' ∈ {0,1}^λ
    tag_i_prime = secrets.randbits(SECURITY_PARAM)
    
    # Step 5: 计算 σ_i' = (HG(i||tag_i') * u^s')^α
    i_tag_prime_concat = str(i) + str(tag_i_prime)
    HG_i_tag_prime = HG(i_tag_prime_concat)  # HG: {0,1}* -> G1
    u_s_prime = u ** s_prime  # u^s' ∈ G1
    HG_i_tag_prime_u_s_prime = HG_i_tag_prime * u_s_prime  # G1 群点加法
    sigma_i_prime = HG_i_tag_prime_u_s_prime ** alpha  # σ_i' ∈ G1（BLS 签名）
    
    # Step 6: 更新 Acc(R) = Acc(R) * HPrime(tag_i) (将旧tag添加到删除集合)
    # 注意：这里实际上是在 Server 端更新，但算法描述中提到了这一步
    # 实际上 Acc(R) 的更新是通过更新 R 集合和 z_star 来实现的
    
    # Server 端操作
    # Step 7: 检查 e(σ_i', g) == e(A, HG(i||tag_i') * u^s')
    e_sigma_prime_g = pair(sigma_i_prime, g)  # e(σ_i', g) ∈ GT
    e_A_HG_u_prime = pair(HG_i_tag_prime_u_s_prime, A)  # e(HG(i||tag_i') * u^s', A) ∈ GT
    if e_sigma_prime_g != e_A_HG_u_prime:
        return None  # 验证失败，返回 ⊥
    
    # Step 8: 更新 DB[i] = (s', σ_i', tag_i')（索引 i 作为字典 key，不需要存储在元组中）
    server_state['DB'][i] = (s_prime, sigma_i_prime, tag_i_prime)
    
    # Step 9: 更新 R = R ∪ {tag_i} (添加旧的 tag_i 到删除集合)
    server_state['R'].add(tag_i)
    
    # Step 10: 调用 update_z_star(server_state, tag_i, n) 更新缓存的 z_star
    update_z_star(server_state, tag_i, n)
    
    # Step 11: 更新 Acc_R = h^z_star mod n（保持一致性）
    h = vk['h']  # RSA accumulator 初始值
    z_star = server_state['z_star']
    server_state['Acc_R'] = pow(h, z_star, n)  # Acc_R = h^z_star mod n
    
    # Step 12: 返回 (s', σ_i', tag_i')
    return (s_prime, sigma_i_prime, tag_i_prime)

