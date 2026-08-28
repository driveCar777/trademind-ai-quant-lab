#!/bin/bash
# Phase 2: Docker 离线安装
# 适用: Jetson AGX Xavier ARM64
# 前置条件: 已下载 docker-24.0.7.tgz

set -e

echo "============================================"
echo "Phase 2: Docker 离线安装 (ARM64)"
echo "============================================"

DOCKER_VERSION="24.0.7"
DOCKER_TGZ="/tmp/docker-${DOCKER_VERSION}.tgz"

# 检查文件是否存在
if [ ! -f "$DOCKER_TGZ" ]; then
    echo "错误: 未找到 $DOCKER_TGZ"
    echo "请从 Windows 传输 docker-${DOCKER_VERSION}.tgz 到 /tmp/"
    exit 1
fi

echo "[1/6] 检查是否已安装 Docker..."
if command -v docker &> /dev/null; then
    echo "Docker 已安装:"
    docker --version
    read -p "是否重新安装? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "跳过 Docker 安装"
        exit 0
    fi
fi

echo "[2/6] 停止现有 Docker 服务..."
sudo systemctl stop docker.socket 2>/dev/null || true
sudo systemctl stop docker.service 2>/dev/null || true

echo "[3/6] 解压 Docker 二进制文件..."
cd /tmp
tar xzf "$DOCKER_TGZ"

echo "[4/6] 复制二进制文件到 /usr/bin/..."
sudo cp docker/* /usr/bin/
sudo chmod +x /usr/bin/docker*

echo "[5/6] 创建 Docker 配置..."
# 创建 docker group
sudo groupadd -f docker
sudo usermod -aG docker $USER

# 创建 systemd service
echo "[5.1] 创建 systemd 服务文件..."
sudo tee /etc/systemd/system/docker.service > /dev/null <<'EOF'
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target firewalld.service
Wants=network-online.target

[Service]
Type=notify
ExecStart=/usr/bin/dockerd
ExecReload=/bin/kill -s HUP $MAINPID
LimitNOFILE=infinity
LimitNPROC=infinity
TimeoutStartSec=0
Delegate=yes
KillMode=process
Restart=on-failure
StartLimitBurst=3
StartLimitInterval=60s

[Install]
WantedBy=multi-user.target
EOF

# 创建 docker group service
sudo tee /etc/systemd/system/docker.socket > /dev/null <<'EOF'
[Unit]
Description=Docker Socket for the API

[Socket]
ListenStream=/var/run/docker.sock
SocketMode=0660
SocketUser=root
SocketGroup=docker

[Install]
WantedBy=sockets.target
EOF

echo "[6/6] 启动 Docker 服务..."
sudo systemctl daemon-reload
sudo systemctl enable docker.service
sudo systemctl start docker.service

# 创建 docker 配置目录
sudo mkdir -p /etc/docker

# 配置 Docker daemon (针对 Xavier 优化)
sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
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
    "max-concurrent-downloads": 1,
    "max-concurrent-uploads": 1
}
EOF

echo "============================================"
echo "Docker 安装完成"
echo "============================================"
echo ""
echo "版本信息:"
docker --version
echo ""
echo "服务状态:"
sudo systemctl status docker.service --no-pager || true
echo ""
echo "重要: 需要重新登录以使用 Docker (不用 sudo)"
echo "或者运行: newgrp docker"
echo ""
echo "测试命令: docker run hello-world"
