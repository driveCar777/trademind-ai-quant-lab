#!/bin/bash
# TradeMind AI Quant Lab v1.0 - 一键部署脚本
# 适用: NVIDIA Jetson AGX Xavier Industrial
# 执行: 在 Xavier 上直接运行此脚本
# 注意: 需要 sudo 权限

set -e

# 配置
PROJECT_NAME="trademind"
INSTALL_DIR="/opt/trademind"
DATA_DIR="/extSSD/trademind-data"
LOG_FILE="/tmp/trademind_install.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo "" | tee -a "$LOG_FILE"
}

# 检查 root 权限
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 sudo 运行此脚本"
        log_error "例如: sudo bash deploy_xavier.sh"
        exit 1
    fi
}

# ============================================
# Phase 0: 系统检查
# ============================================
system_check() {
    log_step "Phase 0: 系统检查"
    
    log_info "检测系统信息..."
    
    # JetPack 版本
    if [ -f /etc/nv_tegra_release ]; then
        JETPACK=$(cat /etc/nv_tegra_release)
        log_info "JetPack版本: $JETPACK"
    else
        log_warn "未检测到 JetPack"
    fi
    
    # Ubuntu 版本
    UBUNTU=$(grep VERSION_ID /etc/os-release | cut -d'"' -f2)
    log_info "Ubuntu版本: $UBUNTU"
    
    # 检查 CUDA
    if command -v nvcc &> /dev/null; then
        CUDA=$(nvcc --version | grep release | awk '{print $5}' | cut -d',' -f1)
        log_info "CUDA版本: $CUDA"
    else
        log_warn "CUDA 未在 PATH 中"
    fi
    
    # 检查网络
    if ping -c 1 8.8.8.8 &> /dev/null; then
        log_info "网络连接: 正常"
    else
        log_error "网络连接失败，请检查网络"
        exit 1
    fi
    
    # 检查 Docker
    if command -v docker &> /dev/null; then
        DOCKER=$(docker --version | awk '{print $3}' | cut -d',' -f1)
        log_info "Docker已安装: $DOCKER"
    else
        log_info "Docker未安装，将自动安装"
    fi
    
    # 检查磁盘空间
    ROOT_FREE=$(df / | tail -1 | awk '{print $4}')
    log_info "系统盘剩余: ${ROOT_FREE}KB"
    
    if [ -d /extSSD ]; then
        SSD_FREE=$(df /extSSD | tail -1 | awk '{print $4}')
        log_info "外置SSD剩余: ${SSD_FREE}KB"
    fi
}

# ============================================
# Phase 1: 创建目录结构
# ============================================
create_directories() {
    log_step "Phase 1: 创建目录结构"
    
    # 创建主目录
    log_info "创建 $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"/{docker,compose,config,data,logs,models,workspace,backup,scripts}
    
    # 创建服务目录
    for service in indicator-worker factor-worker backtest-worker api-gateway; do
        mkdir -p "$INSTALL_DIR/services/$service"
    done
    
    # 创建数据目录 (外置SSD)
    if [ -d /extSSD ]; then
        log_info "创建 $DATA_DIR..."
        mkdir -p "$DATA_DIR"/{market-data,backtest-results,logs,database-backup,cache,redis}
    else
        log_warn "/extSSD 不存在，数据将存储在系统盘"
        mkdir -p "$INSTALL_DIR/data"/{market-data,backtest-results,redis}
        DATA_DIR="$INSTALL_DIR/data"
    fi
    
    # 设置权限
    chown -R dji:dji "$INSTALL_DIR"
    if [ -d /extSSD ]; then
        chown -R dji:dji "$DATA_DIR"
    fi
    
    log_info "目录创建完成"
}

# ============================================
# Phase 2: 安装 Docker
# ============================================
install_docker() {
    log_step "Phase 2: 安装 Docker"
    
    if command -v docker &> /dev/null; then
        log_info "Docker 已安装，跳过"
        return 0
    fi
    
    log_info "安装 Docker (ARM64)..."
    
    # 安装依赖
    apt-get update
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        apt-transport-https \
        software-properties-common
    
    # 添加 Docker 官方 GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # 添加仓库
    echo \
        "deb [arch=arm64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装 Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # 启动 Docker
    systemctl enable docker
    systemctl start docker
    
    # 将 dji 用户加入 docker 组
    usermod -aG docker dji
    
    log_info "Docker 安装完成: $(docker --version)"
}

# ============================================
# Phase 3: 配置 NVIDIA Docker
# ============================================
setup_nvidia_docker() {
    log_step "Phase 3: 配置 NVIDIA Container Runtime"
    
    # 检查是否安装了 nvidia-container-toolkit
    if command -v nvidia-ctk &> /dev/null; then
        log_info "NVIDIA Container Toolkit 已安装"
    else
        log_info "安装 NVIDIA Container Toolkit..."
        
        # 添加 NVIDIA 仓库
        distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
        curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
        curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
            tee /etc/apt/sources.list.d/nvidia-docker.list
        
        apt-get update
        apt-get install -y nvidia-container-toolkit
        
        # 重启 Docker
        systemctl restart docker
    fi
    
    # 配置 Docker daemon
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << 'EOF'
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "storage-driver": "overlay2",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
EOF
    
    systemctl restart docker
    log_info "NVIDIA Docker 配置完成"
    
    # 测试 GPU 访问
    log_info "测试 GPU 访问..."
    if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        log_info "GPU 访问正常"
    else
        log_warn "GPU 测试失败，可能需要 JetPack 特定配置"
    fi
}

# ============================================
# Phase 4: 下载 Docker 镜像
# ============================================
pull_images() {
    log_step "Phase 4: 下载 Docker 镜像"
    
    log_info "下载基础镜像..."
    docker pull redis:7-alpine
    docker pull python:3.10-slim-bookworm
    docker pull prom/node-exporter:latest
    
    # 预下载常用镜像加速
    log_info "预下载 Python 依赖..."
    docker pull python:3.10-bookworm
    
    log_info "镜像下载完成"
}

# ============================================
# Phase 5: 创建服务代码
# ============================================
setup_services() {
    log_step "Phase 5: 创建服务代码"
    
    # Indicator Worker
    log_info "配置 indicator-worker..."
    mkdir -p "$INSTALL_DIR/services/indicator-worker/src"
    
    cat > "$INSTALL_DIR/services/indicator-worker/Dockerfile" << 'EOF'
FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ gfortran libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["python3", "-m", "src.main"]
EOF

    cat > "$INSTALL_DIR/services/indicator-worker/requirements.txt" << 'EOF'
numpy==1.24.3
pandas==2.0.3
scipy==1.11.1
fastapi==0.103.1
uvicorn==0.23.2
redis==5.0.0
loguru==0.7.2
requests==2.31.0
pyyaml==6.0.1
EOF

    # 简化的 indicator main.py
    cat > "$INSTALL_DIR/services/indicator-worker/src/main.py" << 'EOF'
#!/usr/bin/env python3
import os, json
from fastapi import FastAPI
import pandas as pd
import numpy as np
import redis

app = FastAPI(title="Indicator Worker")
r = redis.Redis(host='redis', port=6379, decode_responses=True)

def calc_ema(prices, period=20):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().tolist()

def calc_macd(prices, fast=12, slow=26, signal=9):
    s = pd.Series(prices)
    ema_fast = s.ewm(span=fast, adjust=False).mean()
    ema_slow = s.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return {
        'macd': macd.tolist(),
        'signal': signal_line.tolist(),
        'histogram': (macd - signal_line).tolist()
    }

def calc_rsi(prices, period=14):
    s = pd.Series(prices)
    delta = s.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.tolist()

def calc_boll(prices, period=20, std=2):
    s = pd.Series(prices)
    middle = s.rolling(window=period).mean()
    std_dev = s.rolling(window=period).std()
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    return {
        'middle': middle.tolist(),
        'upper': upper.tolist(),
        'lower': lower.tolist()
    }

@app.get("/health")
def health():
    return {"status": "healthy", "worker": "indicator"}

@app.post("/calculate/{indicator}")
def calculate(indicator: str, data: dict):
    prices = data.get('prices', [])
    if not prices:
        return {"error": "No prices"}
    
    result = {}
    if indicator == "ema":
        result = {"values": calc_ema(prices, data.get('params', {}).get('period', 20))}
    elif indicator == "macd":
        result = calc_macd(prices)
    elif indicator == "rsi":
        result = {"values": calc_rsi(prices)}
    elif indicator == "boll":
        result = calc_boll(prices)
    else:
        return {"error": f"Unknown indicator: {indicator}"}
    
    return {"indicator": indicator, "result": result}
EOF

    touch "$INSTALL_DIR/services/indicator-worker/src/__init__.py"
    
    log_info "服务代码创建完成"
}

# ============================================
# Phase 6: 创建 Docker Compose
# ============================================
create_compose() {
    log_step "Phase 6: 创建 Docker Compose 配置"
    
    cat > "$INSTALL_DIR/compose/docker-compose.yml" << EOF
version: "3.8"

services:
  redis:
    image: redis:7-alpine
    container_name: trademind-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - $DATA_DIR/redis:/data
    command: redis-server --appendonly yes --maxmemory 2gb

  indicator-worker:
    build:
      context: $INSTALL_DIR/services/indicator-worker
      dockerfile: Dockerfile
    container_name: trademind-indicator
    restart: unless-stopped
    environment:
      - REDIS_HOST=redis
    volumes:
      - $DATA_DIR/market-data:/data/market:ro
    depends_on:
      - redis
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 6G

  node-exporter:
    image: prom/node-exporter:latest
    container_name: trademind-monitor
    restart: unless-stopped
    privileged: true
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
    ports:
      - "9100:9100"
EOF

    log_info "Docker Compose 配置完成"
}

# ============================================
# Phase 7: 启动服务
# ============================================
start_services() {
    log_step "Phase 7: 启动 TradeMind 服务"
    
    cd "$INSTALL_DIR/compose"
    
    log_info "构建镜像..."
    docker-compose build --no-cache
    
    log_info "启动服务..."
    docker-compose up -d
    
    log_info "等待服务启动..."
    sleep 10
    
    # 检查状态
    log_info "服务状态:"
    docker-compose ps
    
    # 健康检查
    log_info "健康检查..."
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        log_info "Redis: 正常"
    else
        log_warn "Redis: 可能未就绪"
    fi
}

# ============================================
# Phase 8: 配置开机自启
# ============================================
setup_autostart() {
    log_step "Phase 8: 配置开机自启动"
    
    cat > /etc/systemd/system/trademind.service << EOF
[Unit]
Description=TradeMind AI Quant Lab
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$INSTALL_DIR/compose
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=dji
Group=docker

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable trademind.service
    
    log_info "开机自启配置完成"
}

# ============================================
# 主程序
# ============================================
main() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN} TradeMind AI Quant Lab v1.0 部署程序 ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    check_sudo
    system_check
    create_directories
    install_docker
    setup_nvidia_docker
    pull_images
    setup_services
    create_compose
    start_services
    setup_autostart
    
    log_step "部署完成!"
    echo ""
    echo -e "${GREEN}TradeMind 已成功部署到您的 Xavier!${NC}"
    echo ""
    echo "服务地址:"
    echo "  - Redis:        localhost:6379"
    echo "  - Node Exporter: http://$(hostname -I | awk '{print $1}'):9100"
    echo ""
    echo "管理命令:"
    echo "  cd $INSTALL_DIR/compose && docker-compose logs -f"
    echo "  cd $INSTALL_DIR/compose && docker-compose ps"
    echo "  sudo systemctl status trademind"
    echo ""
    echo "日志文件: $LOG_FILE"
}

# 运行主程序
main "$@"
