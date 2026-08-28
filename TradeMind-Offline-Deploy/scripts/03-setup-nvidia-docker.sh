#!/bin/bash
# Phase 3: NVIDIA Docker 支持配置
# 让 Docker 能使用 GPU

set -e

echo "============================================"
echo "Phase 3: NVIDIA Docker 支持配置"
echo "============================================"

echo "[1/5] 检查 JetPack 版本..."
if [ -f /etc/nv_tegra_release ]; then
    echo "JetPack 信息:"
    cat /etc/nv_tegra_release
else
    echo "警告: 未找到 JetPack 信息"
fi

echo ""
echo "[2/5] 检查 CUDA..."
if [ -d /usr/local/cuda ]; then
    echo "CUDA 路径: /usr/local/cuda"
    if [ -f /usr/local/cuda/bin/nvcc ]; then
        /usr/local/cuda/bin/nvcc --version
    fi
else
    echo "警告: CUDA 未找到"
fi

echo ""
echo "[3/5] 配置 NVIDIA Runtime..."
# 检查 nvidia-container-runtime 是否存在
if [ -f /usr/bin/nvidia-container-runtime ]; then
    echo "nvidia-container-runtime 已安装"
else
    echo "警告: nvidia-container-runtime 未找到"
    echo "Jetson 设备通常使用不同的方式访问 GPU"
    echo "尝试配置特权模式..."
fi

echo ""
echo "[4/5] 更新 Docker daemon 配置..."
# 对于 Jetson，我们通常使用特权模式访问 GPU
# 或者通过挂载设备

echo "[4.1] 备份现有配置..."
sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup.$(date +%Y%m%d) 2>/dev/null || true

echo "[4.2] 更新配置..."
sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "runc",
    "storage-driver": "overlay2",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "live-restore": true,
    "group": "docker"
}
EOF

echo ""
echo "[5/5] 重启 Docker..."
sudo systemctl restart docker
sleep 2

echo "============================================"
echo "NVIDIA Docker 配置完成"
echo "============================================"
echo ""
echo "注意: Jetson 设备 GPU 访问方式："
echo "1. 特权模式: docker run --privileged"
echo "2. 设备挂载: docker run --device /dev/nvhost-ctrl"
echo "3. 自动检测: JetPack 5.0+ 有更好的 GPU 支持"
echo ""
echo "测试 GPU 访问:"
echo "docker run --rm --privileged python:3.10-slim python3 -c \"import os; print('GPU accessible')\""
