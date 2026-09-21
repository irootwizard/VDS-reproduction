#!/bin/bash
# activate_venv.sh - 激活共享的虚拟环境

VENV_PATH="$HOME/crypto-libs-venv"
LIB_PATH="/mnt/d/WorkStation/crypto-libs/local_install/lib"

# 检查并设置 LD_LIBRARY_PATH
if [ -d "$LIB_PATH" ]; then
    export LD_LIBRARY_PATH="$LIB_PATH:$LD_LIBRARY_PATH"
    echo "✓ 已设置 LD_LIBRARY_PATH: $LIB_PATH"
else
    echo "⚠ 警告: 库路径不存在: $LIB_PATH"
    echo "  某些功能可能无法正常工作"
    # 仍然尝试设置，以防路径在其他位置
    export LD_LIBRARY_PATH="$LIB_PATH:$LD_LIBRARY_PATH"
fi

if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✓ 已激活虚拟环境: $VENV_PATH"
    echo "Python 路径: $(which python)"
    
    # 检查 charm 库是否能正常导入
    echo ""
    echo "检查 charm 库..."
    if python -c "from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair; print('✓ charm 库导入成功')" 2>/dev/null; then
        echo "✓ charm 库已正确安装并可正常使用"
    else
        echo "✗ charm 库导入失败"
        echo "  请运行: pip install charm-crypto"
        echo "  或检查 LD_LIBRARY_PATH 是否正确设置"
    fi
else
    echo "✗ 虚拟环境不存在: $VENV_PATH"
    exit 1
fi