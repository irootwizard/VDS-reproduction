"""
CLVC (Commitment-Linked Vector Commitment) 实现
基于双线性配对和多项式承诺
使用 Charm2 库和 BN254 椭圆曲线
"""

import hashlib
import sys

# 尝试导入 charm 库
try:
    from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair
    CHARM_AVAILABLE = True
except ImportError as e:
    CHARM_AVAILABLE = False
    print("警告: charm 库未安装，CLVC 相关功能将无法使用")
    print(f"  导入错误: {e}")
    print("  请安装: pip install charm-crypto")


def H_sha256(x):
    """SHA-256 哈希函数"""
    return hashlib.sha256(str(x).encode()).digest()


def poly_multiply(p1, p2):
    """
    多项式乘法
    p1, p2: 系数列表，从低次到高次 [c0, c1, c2, ...] 表示 c0 + c1*X + c2*X^2 + ...
    返回: 乘积多项式的系数列表
    """
    deg1 = len(p1) - 1
    deg2 = len(p2) - 1
    result = [p1[0] * 0] * (deg1 + deg2 + 1)  # 使用相同类型的零
    for i in range(len(p1)):
        for j in range(len(p2)):
            result[i + j] = result[i + j] + p1[i] * p2[j]
    return result


def poly_divide(p, divisor):
    """
    多项式除法 p / divisor
    p: 被除多项式系数列表
    divisor: 除数的系数列表（应该是单项式，如 [0, 0, ..., 1] 表示 X^k）
    返回: (quotient, remainder) 商和余数的系数列表
    """
    # 找到divisor的最高次项
    divisor_deg = len(divisor) - 1
    zero = p[0] * 0 if len(p) > 0 else 0
    while divisor_deg >= 0 and divisor[divisor_deg] == zero:
        divisor_deg -= 1
    
    if divisor_deg < 0:
        raise ValueError("除数不能为零多项式")
    
    p_deg = len(p) - 1
    while p_deg >= 0 and p[p_deg] == zero:
        p_deg -= 1
    
    if p_deg < divisor_deg:
        return [zero], p[:]
    
    # 初始化商和余数
    quotient = [zero] * (p_deg - divisor_deg + 1)
    remainder = p[:]
    
    # 执行长除法
    for i in range(p_deg, divisor_deg - 1, -1):
        if remainder[i] != zero:
            coeff = remainder[i] / divisor[divisor_deg]
            quotient[i - divisor_deg] = coeff
            # 减去 divisor * coeff * X^(i - divisor_deg)
            for j in range(divisor_deg + 1):
                if j <= i:
                    remainder[i - j] = remainder[i - j] - coeff * divisor[divisor_deg - j]
    
    # 清理前导零
    while len(remainder) > 1 and remainder[-1] == zero:
        remainder.pop()
    while len(quotient) > 1 and quotient[-1] == zero:
        quotient.pop()
    
    return quotient, remainder


def poly_eval_group(p, g_powers, group):
    """
    使用群元素计算多项式在τ处的群元素值
    p: 系数列表 [c0, c1, c2, ...] 表示 c0 + c1*X + c2*X^2 + ...
    g_powers: [g^τ^0, g^τ^1, g^τ^2, ...] 群元素的幂次列表
    group: PairingGroup 实例
    返回: g^{p(τ)} = g^{c0 + c1*τ + c2*τ^2 + ...}
    """
    result = group.init(G1, 1)  # 单位元
    for i, coeff in enumerate(p):
        if i < len(g_powers) and coeff != 0:
            # g^{coeff * τ^i} = (g^τ^i)^{coeff}
            result = result * (g_powers[i] ** coeff)
    return result


def KeyGen(lam, m, group=None):
    """
    Algorithm 1: CLVC.KeyGen(λ, F_IP) → (pp, td)
    
    生成 CLVC 的公钥、验证密钥和陷门
    
    Args:
        lam: 安全参数 λ
        m: 向量大小
        group: PairingGroup 实例（如果为 None，则创建新的）
    
    Returns:
        (pp, td): 
            pp = (prk, vrk): 公钥参数
                prk: 证明密钥 = ({g_1^τ^i, g_2^τ^i}_{i=0}^{m-1})
                vrk: 验证密钥 = (g_1^{τ^{m-1}}, {g_2^τ^i}_{i=0}^{m})
            td: 陷门 = {τ^{i-1}}_{i=1}^{m}
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    if group is None:
        group = PairingGroup('BN254')
    
    # 生成生成元
    g_1 = group.random(G1)
    g_2 = group.random(G2)
    
    # 选择随机整数 τ ∈ Z_p
    tau = group.random(ZR)
    
    # 计算 prk = ({g_1^τ^i, g_2^τ^i}_{i=0}^{m-1})
    prk_g1 = []
    prk_g2 = []
    for i in range(m):
        tau_power = tau ** i
        prk_g1.append(g_1 ** tau_power)  # g_1^τ^i
        prk_g2.append(g_2 ** tau_power)  # g_2^τ^i
    
    prk = {
        'g1_powers': prk_g1,  # {g_1^τ^i}_{i=0}^{m-1}
        'g2_powers': prk_g2   # {g_2^τ^i}_{i=0}^{m-1}
    }
    
    # 计算 vrk = (g_1^{τ^{m-1}}, {g_2^τ^i}_{i=0}^{m})
    tau_m_minus_1 = tau ** (m - 1)
    vrk_g1 = g_1 ** tau_m_minus_1  # g_1^{τ^{m-1}}
    
    vrk_g2 = []
    for i in range(m + 1):
        tau_power = tau ** i
        vrk_g2.append(g_2 ** tau_power)  # {g_2^τ^i}_{i=0}^{m}
    
    vrk = {
        'g1_tau_m_minus_1': vrk_g1,  # g_1^{τ^{m-1}}
        'g2_powers': vrk_g2           # {g_2^τ^i}_{i=0}^{m}
    }
    
    # 计算 td = {τ^{i-1}}_{i=1}^{m}
    td = []
    for i in range(1, m + 1):
        tau_power = tau ** (i - 1)
        td.append(tau_power)
    
    pp = {
        'prk': prk,
        'vrk': vrk,
        'group': group,
        'g1': g_1,
        'g2': g_2,
        'm': m
    }
    
    return pp, td


def Commit(prk, v, group):
    """
    Algorithm 2: CLVC.Commit(prk, v) → (C, aux)
    
    对向量 v 进行承诺
    
    Args:
        prk: 证明密钥
        v: 向量 v = (a_1, ..., a_m)，长度为 m
        group: PairingGroup 实例
    
    Returns:
        (C, aux):
            C: 承诺 = g_1^{V(τ)} · g_1^r
            aux: 辅助信息 = (a_1, ..., a_m; r)
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    m = len(v)
    g1_powers = prk['g1_powers']
    g_1 = g1_powers[0]  # g_1^τ^0 = g_1
    
    # 计算 g_1^{V(τ)}，其中 V(X) = ∑_{i=1}^{m} a_i · X^{i-1}
    # V(τ) = ∑_{i=1}^{m} a_i · τ^{i-1}
    # g_1^{V(τ)} = ∏_{i=1}^{m} (g_1^τ^{i-1})^{a_i}
    # 注意：v[i] = a_{i+1}，对应 τ^i = τ^{(i+1)-1}
    # 所以 v[0] = a_1 对应 τ^0，v[1] = a_2 对应 τ^1，...
    g1_V_tau = group.init(G1, 1)  # 单位元
    for i in range(m):
        a_i = v[i]  # a_{i+1}
        # v[i] = a_{i+1} 对应 τ^i，使用 g_1^τ^i
        g1_power = g1_powers[i]  # g_1^τ^i
        g1_V_tau = g1_V_tau * (g1_power ** a_i)
    
    # 选择随机整数 r ∈ Z_p
    r = group.random(ZR)
    
    # 计算 C = g_1^{V(τ)} · g_1^r
    g1_r = g_1 ** r
    C = g1_V_tau * g1_r
    
    # aux = (a_1, ..., a_m; r)
    aux = {
        'a': v.copy(),  # (a_1, ..., a_m)
        'r': r
    }
    
    return C, aux


def Open(prk, aux, b, y, group):
    """
    Algorithm 3: CLVC.Open(prk, aux, b, y) → π
    
    生成证明（不使用tau，仅使用prk中的群元素）
    
    Args:
        prk: 证明密钥
        aux: 辅助信息 = (a_1, ..., a_m; r)
        b: 查询向量 b = (b_1, ..., b_m)
        y: 内积值 y = <v, b> = ∑_{i=1}^{m} a_i · b_i
        group: PairingGroup 实例
    
    Returns:
        π: 证明 = (g_1^{R(τ)}, g_1^{H(τ)}, g_1^{R̂(τ)}, g_1^r)
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    a = aux['a']  # (a_1, ..., a_m)
    r = aux['r']
    m = len(a)
    
    g1_powers = prk['g1_powers']  # {g_1^τ^i}_{i=0}^{m-1}
    g_1 = g1_powers[0]
    
    # 构建多项式 V(X) = ∑_{i=1}^{m} a_i · X^{i-1}
    # 系数：[a_1, a_2, ..., a_m] 对应 [X^0, X^1, ..., X^{m-1}]
    V_coeffs = [group.init(ZR, a_i) for a_i in a]
    
    # 构建多项式 B(X) = ∑_{i=1}^{m} b_i · X^{m-i}
    # 系数：[b_m, b_{m-1}, ..., b_1] 对应 [X^0, X^1, ..., X^{m-1}]
    B_coeffs = [group.init(ZR, 0)] * m
    for i in range(m):
        B_coeffs[m - 1 - i] = group.init(ZR, b[i])  # b_{i+1} 对应 X^{m-i-1}
    
    # 计算 (V(X) + r) · B(X)
    # V(X) + r 的系数：[a_1 + r, a_2, ..., a_m]（实际上r是常数项）
    V_plus_r_coeffs = V_coeffs[:]
    if len(V_plus_r_coeffs) > 0:
        V_plus_r_coeffs[0] = V_plus_r_coeffs[0] + r
    else:
        V_plus_r_coeffs = [r]
    
    # 多项式乘法 (V(X) + r) · B(X)
    V_plus_r_B_coeffs = poly_multiply(V_plus_r_coeffs, B_coeffs)
    
    # 计算 (y + r·b_1) · X^{m-1} 的系数
    b_1 = b[0] if len(b) > 0 else group.init(ZR, 0)
    y_plus_r_b1 = y + r * b_1
    y_term_coeffs = [group.init(ZR, 0)] * (m - 1) + [y_plus_r_b1]
    
    # 计算 P(X) = (V(X) + r) · B(X) - (y + r·b_1) · X^{m-1}
    # 需要对齐次数
    max_deg = max(len(V_plus_r_B_coeffs), len(y_term_coeffs))
    P_coeffs = [group.init(ZR, 0)] * max_deg
    for i in range(len(V_plus_r_B_coeffs)):
        P_coeffs[i] = V_plus_r_B_coeffs[i]
    for i in range(len(y_term_coeffs)):
        P_coeffs[i] = P_coeffs[i] - y_term_coeffs[i]
    
    # 将 P(X) 除以 X^m，得到商 H(X) 和余数 R(X)
    # X^m 的系数：[0, 0, ..., 0, 1] (m个0，然后1)
    X_m_coeffs = [group.init(ZR, 0)] * m + [group.init(ZR, 1)]
    
    H_coeffs, R_coeffs = poly_divide(P_coeffs, X_m_coeffs)
    
    # 确保 R 的次数 < m - 1
    while len(R_coeffs) >= m:
        R_coeffs = R_coeffs[:m-1]
    
    # 使用群元素计算 g_1^{R(τ)}，不使用tau
    # R(X) = r_0 + r_1*X + ... + r_{m-2}*X^{m-2}
    # g_1^{R(τ)} = g_1^{r_0} * (g_1^τ)^{r_1} * ... * (g_1^{τ^{m-2}})^{r_{m-2}}
    g1_R_tau = poly_eval_group(R_coeffs, g1_powers, group)
    
    # 计算 g_1^{H(τ)}
    # H(X) 的次数可能较高，需要扩展g1_powers或使用其他方法
    # 但H(X)的系数在ZR中，我们可以使用g1_powers来计算
    # 如果H(X)的次数超过m-1，我们需要计算更高次幂
    # 但根据算法，H(X)是P(X)/X^m的商，次数应该不会太高
    # 为了安全，我们计算到需要的次数
    max_h_deg = len(H_coeffs) - 1
    if max_h_deg >= len(g1_powers):
        # 需要更高次幂，但prk中只有到m-1次
        # 实际上，H(X)的次数应该不会超过某个范围
        # 这里我们假设H(X)的次数在合理范围内
        raise ValueError(f"H(X)的次数{max_h_deg}超过prk提供的幂次范围{len(g1_powers)-1}")
    
    g1_H_tau = poly_eval_group(H_coeffs, g1_powers, group)
    
    # 计算 g_1^{R̂(τ)} = g_1^{τ·R(τ)}
    # R̂(X) = X·R(X)，所以 R̂(τ) = τ·R(τ)
    # g_1^{R̂(τ)} = g_1^{τ·R(τ)} = (g_1^τ)^{R(τ)}
    # 但我们需要R(τ)的值，而我们不能直接计算
    # 实际上，R̂(X) = X·R(X) = r_0*X + r_1*X^2 + ... + r_{m-2}*X^{m-1}
    # 所以 g_1^{R̂(τ)} = (g_1^τ)^{r_0} * (g_1^{τ^2})^{r_1} * ... * (g_1^{τ^{m-1}})^{r_{m-2}}
    R_hat_coeffs = [group.init(ZR, 0)] + R_coeffs  # X·R(X)的系数，左移一位
    if len(R_hat_coeffs) > len(g1_powers):
        R_hat_coeffs = R_hat_coeffs[:len(g1_powers)]
    g1_R_hat_tau = poly_eval_group(R_hat_coeffs, g1_powers, group)
    
    # g_1^r
    g1_r = g_1 ** r
    
    # π = (g_1^{R(τ)}, g_1^{H(τ)}, g_1^{R̂(τ)}, g_1^r)
    pi = {
        'g1_R_tau': g1_R_tau,
        'g1_H_tau': g1_H_tau,
        'g1_R_hat_tau': g1_R_hat_tau,
        'g1_r': g1_r
    }
    
    return pi


def Verify(vrk, C, b, y, pi, group):
    """
    Algorithm 4: CLVC.Verify(vrk, C, b, y, π) → 0/1
    
    验证证明
    
    Args:
        vrk: 验证密钥
        C: 承诺
        b: 查询向量 b = (b_1, ..., b_m)
        y: 内积值 y
        pi: 证明 π = (g_1^{R(τ)}, g_1^{H(τ)}, g_1^{R̂(τ)}, g_1^r)
        group: PairingGroup 实例
    
    Returns:
        0 或 1：验证结果
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    m = len(b)
    g2_powers = vrk['g2_powers']  # {g_2^τ^i}_{i=0}^{m}
    g1_tau_m_minus_1 = vrk['g1_tau_m_minus_1']  # g_1^{τ^{m-1}}
    g_2 = g2_powers[0]  # g_2^τ^0 = g_2
    
    # 解析证明
    g1_R_tau = pi['g1_R_tau']
    g1_H_tau = pi['g1_H_tau']
    g1_R_hat_tau = pi['g1_R_hat_tau']
    g1_r = pi['g1_r']
    
    # 计算 C_b = g_1^{∑_{i=1}^{m} b_i·τ^{m-i}}
    # B(X) = ∑_{i=1}^{m} b_i · X^{m-i}
    # C_b = g_1^{B(τ)} = g_1^{∑_{i=1}^{m} b_i·τ^{m-i}}
    # 注意：b_i 对应 τ^{m-i}，所以 b_1 对应 τ^{m-1}，b_2 对应 τ^{m-2}，...，b_m 对应 τ^0
    # 我们需要从vrk中获取g_1^τ^i，但vrk只有g_2^τ^i和g_1^{τ^{m-1}}
    # 实际上，我们需要计算g_1^{B(τ)}，但我们只有g_2^τ^i
    # 根据算法，C_b应该用g_1计算，但验证时我们使用配对
    
    # 实际上，根据算法描述，我们需要计算：
    # e(C, C_b) / (e(g_1^{y·τ^{m-1}}, g_2) · e(g_1^r, g_2^{b_1·τ^{m-1}}))
    # = e(g_1^{R(τ)}, g_2) · e(g_1^{H(τ)}, g_2^{τ^m})
    
    # 计算 g_1^{y·τ^{m-1}} = (g_1^{τ^{m-1}})^y
    g1_y_tau_m_minus_1 = g1_tau_m_minus_1 ** y
    
    # 计算 g_2^{b_1·τ^{m-1}} = (g_2^τ^{m-1})^{b_1}
    b_1 = b[0] if len(b) > 0 else group.init(ZR, 0)
    if m - 1 < len(g2_powers):
        g2_tau_m_minus_1 = g2_powers[m - 1]  # g_2^τ^{m-1}
        g2_b1_tau_m_minus_1 = g2_tau_m_minus_1 ** b_1
    else:
        # 如果索引超出，需要计算
        raise ValueError(f"g2_powers长度不足，需要索引{m-1}")
    
    # 计算 g_2^{τ^m}
    if m < len(g2_powers):
        g2_tau_m = g2_powers[m]  # g_2^τ^m
    else:
        raise ValueError(f"g2_powers长度不足，需要索引{m}")
    
    # 验证第一个等式：
    # e(C, C_b) / (e(g_1^{y·τ^{m-1}}, g_2) · e(g_1^r, g_2^{b_1·τ^{m-1}}))
    # = e(g_1^{R(τ)}, g_2) · e(g_1^{H(τ)}, g_2^{τ^m})
    
    # 计算 C_b = g_1^{B(τ)} = g_1^{∑_{i=1}^{m} b_i·τ^{m-i}}
    # 我们需要从prk或vrk中获取g_1^τ^i，但vrk中没有g_1^τ^i（除了g_1^{τ^{m-1}}）
    # 实际上，根据算法，C_b应该用g_1计算，但验证时我们使用配对，所以我们需要另一种方法
    
    # 重新审视算法：实际上C_b的计算需要g_1^τ^i，但vrk中只有g_2^τ^i
    # 这意味着我们需要从其他地方获取，或者算法描述有误
    
    # 根据算法描述，C_b = g_1^{∑_{i=1}^{m} b_i·τ^{m-i}}
    # 但vrk中没有足够的g_1^τ^i来计算
    # 实际上，我们需要从prk中获取，或者修改算法
    
    # 临时解决方案：假设C_b可以从prk计算（需要修改函数签名）
    # 或者，我们可以通过配对来间接验证
    
    # 实际上，让我重新看算法：验证算法只需要vrk，所以C_b应该可以从vrk计算
    # 但vrk中只有g_1^{τ^{m-1}}和g_2^τ^i
    
    # 根据算法描述，C_b的计算可能需要额外的信息
    # 让我们假设我们需要从prk中获取g_1^τ^i，或者修改验证算法
    
    # 为了完整性，我们假设C_b已经提供或者可以从prk计算
    # 这里我们提供一个需要prk的版本，或者修改为接受C_b作为参数
    
    # 实际上，根据算法，验证应该只需要vrk
    # 让我们检查算法描述：C_b = g_1^{∑_{i=1}^{m} b_i·τ^{m-i}}
    # 这需要g_1^τ^i，但vrk中没有
    
    # 我注意到算法可能需要在验证时计算C_b，但这需要g_1^τ^i
    # 一个可能的解决方案是：C_b可以从prk计算，但prk不应该在验证时使用
    
    # 让我重新检查：实际上，验证算法可能需要prk来计算C_b
    # 或者，C_b应该作为输入提供
    
    # 根据标准实现，我们假设需要prk来计算C_b
    # 或者修改函数签名接受C_b
    
    # 为了匹配算法描述，我们需要prk来计算C_b
    # 修改函数签名，接受prk作为参数
    raise ValueError("Verify需要prk来计算C_b，请使用Verify_with_prk函数")


def Verify_with_prk(vrk, prk, C, b, y, pi, group):
    """
    Algorithm 4: CLVC.Verify(vrk, C, b, y, π) → 0/1
    
    验证证明（需要prk来计算C_b）
    
    Args:
        vrk: 验证密钥
        prk: 证明密钥（用于计算C_b）
        C: 承诺
        b: 查询向量 b = (b_1, ..., b_m)
        y: 内积值 y
        pi: 证明 π = (g_1^{R(τ)}, g_1^{H(τ)}, g_1^{R̂(τ)}, g_1^r)
        group: PairingGroup 实例
    
    Returns:
        0 或 1：验证结果
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    m = len(b)
    g2_powers = vrk['g2_powers']  # {g_2^τ^i}_{i=0}^{m}
    g1_tau_m_minus_1 = vrk['g1_tau_m_minus_1']  # g_1^{τ^{m-1}}
    g_2 = g2_powers[0]  # g_2^τ^0 = g_2
    g1_powers = prk['g1_powers']  # {g_1^τ^i}_{i=0}^{m-1}
    g_1 = g1_powers[0]
    
    # 解析证明
    g1_R_tau = pi['g1_R_tau']
    g1_H_tau = pi['g1_H_tau']
    g1_R_hat_tau = pi['g1_R_hat_tau']
    g1_r = pi['g1_r']
    
    # 计算 C_b = g_1^{∑_{i=1}^{m} b_i·τ^{m-i}}
    # B(X) = ∑_{i=1}^{m} b_i · X^{m-i}
    # b_1 对应 τ^{m-1}，b_2 对应 τ^{m-2}，...，b_m 对应 τ^0
    C_b = group.init(G1, 1)  # 单位元
    for i in range(m):
        b_i = b[i]  # b_{i+1}
        # b_{i+1} 对应 τ^{m-i-1}
        tau_power_idx = m - 1 - i
        if tau_power_idx < len(g1_powers):
            g1_tau_power = g1_powers[tau_power_idx]  # g_1^τ^{m-i-1}
            C_b = C_b * (g1_tau_power ** b_i)
        else:
            raise ValueError(f"g1_powers长度不足，需要索引{tau_power_idx}")
    
    # 计算 g_1^{y·τ^{m-1}} = (g_1^{τ^{m-1}})^y
    g1_y_tau_m_minus_1 = g1_tau_m_minus_1 ** y
    
    # 计算 g_2^{b_1·τ^{m-1}} = (g_2^τ^{m-1})^{b_1}
    b_1 = b[0] if len(b) > 0 else group.init(ZR, 0)
    if m - 1 < len(g2_powers):
        g2_tau_m_minus_1 = g2_powers[m - 1]  # g_2^τ^{m-1}
        g2_b1_tau_m_minus_1 = g2_tau_m_minus_1 ** b_1
    else:
        raise ValueError(f"g2_powers长度不足，需要索引{m-1}")
    
    # 计算 g_2^{τ^m}
    if m < len(g2_powers):
        g2_tau_m = g2_powers[m]  # g_2^τ^m
    else:
        raise ValueError(f"g2_powers长度不足，需要索引{m}")
    
    # 验证第一个等式：
    # e(C, C_b) / (e(g_1^{y·τ^{m-1}}, g_2) · e(g_1^r, g_2^{b_1·τ^{m-1}}))
    # = e(g_1^{R(τ)}, g_2) · e(g_1^{H(τ)}, g_2^{τ^m})
    left_pair1 = pair(C, C_b)
    left_pair2 = pair(g1_y_tau_m_minus_1, g_2)
    left_pair3 = pair(g1_r, g2_b1_tau_m_minus_1)
    left_side = left_pair1 / (left_pair2 * left_pair3)
    
    right_pair1 = pair(g1_R_tau, g_2)
    right_pair2 = pair(g1_H_tau, g2_tau_m)
    right_side = right_pair1 * right_pair2
    
    # 验证第二个等式：e(g_1^{R(τ)}, g_2^τ) = e(g_1^{R̂(τ)}, g_2)
    if 1 < len(g2_powers):
        g2_tau = g2_powers[1]  # g_2^τ
        eq2_left = pair(g1_R_tau, g2_tau)
        eq2_right = pair(g1_R_hat_tau, g_2)
        eq2_valid = (eq2_left == eq2_right)
    else:
        raise ValueError("g2_powers长度不足，需要索引1")
    
    # 两个等式都成立则返回1，否则返回0
    eq1_valid = (left_side == right_side)
    
    return 1 if (eq1_valid and eq2_valid) else 0


def Coll(C, i, a_i, a_prime_i, td, aux, group):
    """
    Algorithm 5: CLVC.Coll(C, i, a_i, a'_i, td, aux) → aux'
    
    碰撞更新辅助信息
    
    Args:
        C: 承诺
        i: 要更新的位置索引（1-based，即第i个元素）
        a_i: 旧值 a_i
        a_prime_i: 新值 a'_i
        td: 陷门 {τ^{i-1}}_{i=1}^{m}
        aux: 旧辅助信息
        group: PairingGroup 实例
    
    Returns:
        aux': 新辅助信息
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    # 转换为0-based索引
    idx = i - 1
    if idx < 0 or idx >= len(td):
        raise ValueError(f"索引{i}超出范围")
    
    r = aux['r']
    a = aux['a'].copy()
    
    # 计算 r' = r + (a_i - a'_i) · τ^{i-1}
    tau_power = td[idx]  # τ^{i-1}
    r_prime = r + (a_i - a_prime_i) * tau_power
    
    # 更新向量
    a[idx] = a_prime_i
    
    # aux' = (a_1, ..., a'_i, ..., a_m; r')
    aux_prime = {
        'a': a,
        'r': r_prime
    }
    
    return aux_prime


def UpComm(prk, C, a_prime_i, a_i, i, group):
    """
    Algorithm 6: CLVC.UpComm(prk, C, a'_i, a_i) → C'
    
    更新承诺
    
    Args:
        prk: 证明密钥
        C: 旧承诺
        a_prime_i: 新值 a'_i
        a_i: 旧值 a_i
        i: 位置索引（1-based）
        group: PairingGroup 实例
    
    Returns:
        C': 新承诺
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    # 转换为0-based索引
    idx = i - 1
    g1_powers = prk['g1_powers']
    
    if idx < 0 or idx >= len(g1_powers):
        raise ValueError(f"索引{i}超出范围")
    
    # 计算 C' = C · g_1^{((a'_i - a_i)·τ^{i-1})}
    # g_1^τ^{i-1} 在 g1_powers[idx] 中
    g1_tau_power = g1_powers[idx]  # g_1^τ^{i-1}
    diff = a_prime_i - a_i
    C_prime = C * (g1_tau_power ** diff)
    
    return C_prime


def UpOpen(a_prime_i, a_i, C, b, y, e_i, pi, prk, aux, group):
    """
    Algorithm 7: CLVC.UpOpen(a'_i, a_i, C, b, y, e_i, π) → π'
    
    更新证明（不使用tau，仅使用prk中的群元素）
    
    Args:
        a_prime_i: 新值 a'_i
        a_i: 旧值 a_i
        C: 承诺
        b: 查询向量 b = (b_1, ..., b_m)
        y: 旧内积值 y
        e_i: 单位向量 e_i（第i个位置为1，其他为0）
        pi: 旧证明 π
        prk: 证明密钥
        aux: 辅助信息（用于获取r'）
        group: PairingGroup 实例
    
    Returns:
        π': 新证明
    """
    if not CHARM_AVAILABLE:
        raise ImportError("charm 库未安装")
    
    m = len(b)
    g1_powers = prk['g1_powers']
    g_1 = g1_powers[0]
    
    # 计算 y' = y + (a'_i - a_i) · e_i · b
    # e_i · b = b_i（内积）
    # 找到e_i对应的位置
    i = None
    for j in range(len(e_i)):
        if e_i[j] != 0:
            i = j + 1  # 转换为1-based
            break
    
    if i is None:
        raise ValueError("e_i中必须有一个非零元素")
    
    b_i = b[i - 1] if i - 1 < len(b) else group.init(ZR, 0)
    y_prime = y + (a_prime_i - a_i) * b_i
    
    # 获取新的r'（从aux中，应该已经通过Coll更新）
    r_prime = aux['r']
    a = aux['a']
    
    # 构建新的多项式 V'(X) = V(X) + (a'_i - a_i) · X^{i-1}
    # V'(X) = V(X) + (a'_i - a_i) · X^{i-1}
    # 所以 V'(X) + r' = V(X) + r' + (a'_i - a_i) · X^{i-1}
    
    # 构建多项式 B(X) = ∑_{j=1}^{m} b_j · X^{m-j}
    B_coeffs = [group.init(ZR, 0)] * m
    for j in range(m):
        B_coeffs[m - 1 - j] = group.init(ZR, b[j])
    
    # 构建 V'(X) + r' 的系数
    V_prime_plus_r_prime_coeffs = [group.init(ZR, a_j) for a_j in a]
    if len(V_prime_plus_r_prime_coeffs) > 0:
        V_prime_plus_r_prime_coeffs[0] = V_prime_plus_r_prime_coeffs[0] + r_prime
    else:
        V_prime_plus_r_prime_coeffs = [r_prime]
    
    # 计算 (V'(X) + r' + (a'_i - a_i) · X^{i-1}) · B(X) - y' · X^{m-1}
    # 首先计算 (a'_i - a_i) · X^{i-1} 的系数
    diff_coeffs = [group.init(ZR, 0)] * (i - 1) + [group.init(ZR, a_prime_i - a_i)]
    V_prime_plus_r_prime_coeffs_extended = V_prime_plus_r_prime_coeffs[:]
    # 扩展以匹配次数
    while len(V_prime_plus_r_prime_coeffs_extended) < len(diff_coeffs):
        V_prime_plus_r_prime_coeffs_extended.append(group.init(ZR, 0))
    for j in range(len(diff_coeffs)):
        if j < len(V_prime_plus_r_prime_coeffs_extended):
            V_prime_plus_r_prime_coeffs_extended[j] = V_prime_plus_r_prime_coeffs_extended[j] + diff_coeffs[j]
        else:
            V_prime_plus_r_prime_coeffs_extended.append(diff_coeffs[j])
    
    # 计算 (V'(X) + r' + (a'_i - a_i) · X^{i-1}) · B(X)
    V_prime_B_coeffs = poly_multiply(V_prime_plus_r_prime_coeffs_extended, B_coeffs)
    
    # 计算 y' · X^{m-1} 的系数
    y_prime_term_coeffs = [group.init(ZR, 0)] * (m - 1) + [y_prime]
    
    # 计算 P'(X) = (V'(X) + r' + (a'_i - a_i) · X^{i-1}) · B(X) - y' · X^{m-1}
    max_deg = max(len(V_prime_B_coeffs), len(y_prime_term_coeffs))
    P_prime_coeffs = [group.init(ZR, 0)] * max_deg
    for j in range(len(V_prime_B_coeffs)):
        P_prime_coeffs[j] = V_prime_B_coeffs[j]
    for j in range(len(y_prime_term_coeffs)):
        P_prime_coeffs[j] = P_prime_coeffs[j] - y_prime_term_coeffs[j]
    
    # 将 P'(X) 除以 X^m，得到商 H'(X) 和余数 R'(X)
    X_m_coeffs = [group.init(ZR, 0)] * m + [group.init(ZR, 1)]
    H_prime_coeffs, R_prime_coeffs = poly_divide(P_prime_coeffs, X_m_coeffs)
    
    # 确保 R' 的次数 < m - 1
    while len(R_prime_coeffs) >= m:
        R_prime_coeffs = R_prime_coeffs[:m-1]
    
    # 使用群元素计算 g_1^{R'(τ)}，不使用tau
    g1_R_prime_tau = poly_eval_group(R_prime_coeffs, g1_powers, group)
    
    # 计算 g_1^{H'(τ)}
    max_h_prime_deg = len(H_prime_coeffs) - 1
    if max_h_prime_deg >= len(g1_powers):
        raise ValueError(f"H'(X)的次数{max_h_prime_deg}超过prk提供的幂次范围{len(g1_powers)-1}")
    
    g1_H_prime_tau = poly_eval_group(H_prime_coeffs, g1_powers, group)
    
    # 计算 g_1^{R̂'(τ)} = g_1^{τ·R'(τ)}
    # R̂'(X) = X·R'(X)，所以 R̂'(τ) = τ·R'(τ)
    # g_1^{R̂'(τ)} = g_1^{τ·R'(τ)} = (g_1^τ)^{R'(τ)}
    # R̂'(X) = X·R'(X) = r'_0*X + r'_1*X^2 + ... + r'_{m-2}*X^{m-1}
    R_hat_prime_coeffs = [group.init(ZR, 0)] + R_prime_coeffs  # X·R'(X)的系数，左移一位
    if len(R_hat_prime_coeffs) > len(g1_powers):
        R_hat_prime_coeffs = R_hat_prime_coeffs[:len(g1_powers)]
    g1_R_hat_prime_tau = poly_eval_group(R_hat_prime_coeffs, g1_powers, group)
    
    # g_1^{r'}
    g1_r_prime = g_1 ** r_prime
    
    # π' = (g_1^{R'(τ)}, g_1^{H'(τ)}, g_1^{R̂'(τ)}, g_1^{r'})
    pi_prime = {
        'g1_R_tau': g1_R_prime_tau,
        'g1_H_tau': g1_H_prime_tau,
        'g1_R_hat_tau': g1_R_hat_prime_tau,
        'g1_r': g1_r_prime
    }
    
    return pi_prime