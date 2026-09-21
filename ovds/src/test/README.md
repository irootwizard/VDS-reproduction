# VADS 测试套件

本目录包含 VADS 协议的完整测试套件，按照函数实现顺序组织。

## 测试文件

1. **test_setup.py** - 测试系统初始化
   - 验证 setup 函数的返回值结构
   - 检查验证密钥、秘密密钥和服务器状态

2. **test_append.py** - 测试数据添加
   - 使用 setup 初始化系统
   - 测试 append 函数添加数据项
   - 验证数据库状态和计数器

3. **test_query.py** - 测试单次查询
   - 使用 setup 和 append 生成数据
   - 测试 query 函数查询数据项
   - 验证返回值和证明结构

4. **test_verify.py** - 测试单次查询验证
   - 使用 setup、append 和 query 生成数据
   - 测试 verify 函数验证查询证明
   - 验证验证结果和错误处理

5. **test_query_star.py** - 测试并发查询
   - 使用 setup 和 append 生成多个数据项
   - 测试 query_star 函数并发查询
   - 验证聚合证明结构

6. **test_verify_star.py** - 测试并发查询验证
   - 使用 setup、append 和 query_star 生成数据
   - 测试 verify_star 函数验证并发查询证明
   - 验证验证结果和错误处理

7. **test_audit.py** - 测试数据审计
   - 使用 setup 和 append 生成多个数据项
   - 测试 audit 函数进行数据审计
   - 验证审计证明结构

8. **test_judge.py** - 测试审计评判
   - 使用 setup、append 和 audit 生成数据
   - 测试 judge 函数验证审计证明
   - 验证验证结果和错误处理

9. **test_all.py** - 运行所有测试
   - 按顺序运行所有测试
   - 生成测试总结报告

## 运行测试

### 运行单个测试

```bash
# 测试 setup 函数
python src/test/test_setup.py

# 测试 append 函数
python src/test/test_append.py

# 测试 query 函数
python src/test/test_query.py

# 测试 verify 函数
python src/test/test_verify.py

# 测试 query_star 函数
python src/test/test_query_star.py

# 测试 verify_star 函数
python src/test/test_verify_star.py

# 测试 audit 函数
python src/test/test_audit.py

# 测试 judge 函数
python src/test/test_judge.py
```

### 运行所有测试

```bash
python src/test/test_all.py
```

## 测试策略

每个测试文件都遵循以下策略：

1. **逐步生成数据**：按照 VADS 协议的实际流程，先调用 setup，然后逐步调用后续函数
2. **验证单个函数**：每个测试文件专注于测试一个函数，使用前面函数生成的数据
3. **完整验证**：验证返回值、数据结构、边界情况和错误处理

## 依赖

- Python 3.x
- charm-crypto 库（用于双线性配对）
- RSA-accumulator 模块

## 注意事项

- 确保已安装 charm-crypto：`pip install charm-crypto`
- 测试需要 RSA-accumulator 模块在正确路径
- 某些测试可能需要较长时间（RSA 密钥生成）

