#!/bin/bash
# activate_venv.sh - 激活共享的虚拟环境

# 虚拟环境路径：优先使用环境变量 VENV_PATH，否则默认 ~/crypto-libs-venv
VENV_PATH="${VENV_PATH:-$HOME/crypto-libs-venv}"

# PBC 库路径：优先使用环境变量 LIB_PATH，否则自动探测常见位置
if [ -z "$LIB_PATH" ]; then
    # 探测 Windows 挂载盘下的 crypto-libs（兼容目录移动后的情况）
    for candidate in \
        "/mnt/d/WorkStation/crypto-libs/local_install/lib" \
        "/mnt/c/WorkStation/crypto-libs/local_install/lib" \
        "/usr/local/lib" \
        "/usr/lib"
    do
        if [ -d "$candidate" ] && ls "$candidate"/libpbc* &>/dev/null 2>&1; then
            LIB_PATH="$candidate"
            break
        fi
    done
fi

if [ -n "$LIB_PATH" ]; then
    export LD_LIBRARY_PATH="$LIB_PATH:$LD_LIBRARY_PATH"
    echo "✓ 已设置 LD_LIBRARY_PATH: $LIB_PATH"
else
    echo "⚠ 未找到 PBC 库路径，charm 可能无法加载"
    echo "  可手动设置: export LIB_PATH=/path/to/lib && source activate_venv.sh"
fi

if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✓ 已激活虚拟环境: $VENV_PATH"
    echo "  Python 路径: $(which python)"

    echo ""
    echo "检查 charm 库..."
    if python -c "from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair; print('✓ charm 库导入成功')" 2>/dev/null; then
        echo "✓ charm 库已正确安装并可正常使用"
    else
        echo "✗ charm 库导入失败"
        echo "  请参考 README.md 安装依赖"
    fi
else
    echo "✗ 虚拟环境不存在: $VENV_PATH"
    echo "  请参考 README.md 创建虚拟环境"
    exit 1
fi