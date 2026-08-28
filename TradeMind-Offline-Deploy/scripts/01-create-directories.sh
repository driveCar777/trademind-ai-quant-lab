#!/bin/bash
# Phase 1: 创建标准目录结构
# 执行时间: 约 10 秒
# 安全性: 高 - 只创建目录，不修改系统

echo "============================================"
echo "Phase 1: 创建 TradeMind 标准目录结构"
echo "============================================"

# 检查是否 root 或 sudo 权限
if [ "$EUID" -ne 0 ]; then 
    echo "注意: 使用普通用户权限创建目录"
    SUDO="sudo"
else
    echo "注意: 使用 root 权限"
    SUDO=""
fi

# 主目录 - 系统盘
echo "[1/3] 创建 /opt/trademind 目录..."
$SUDO mkdir -p /opt/trademind/{docker,compose,config,data,logs,models,workspace,backup,scripts}
$SUDO mkdir -p /opt/trademind/docker/{images,build-cache}

# 数据目录 - 外置SSD
echo "[2/3] 创建 /extSSD/trademind-data 目录..."
$SUDO mkdir -p /extSSD/trademind-data/{market-data,backtest-results,logs,database-backup,cache}

# Services 目录
echo "[3/3] 创建 services 目录..."
$SUDO mkdir -p /opt/trademind/services/{indicator-worker,factor-worker,backtest-worker,monitor-agent,api-gateway}

# 设置权限
echo "设置目录权限..."
$SUDO chown -R $(whoami):$(whoami) /opt/trademind 2>/dev/null || true
$SUDO chmod 755 /opt/trademind

$SUDO chown -R $(whoami):$(whoami) /extSSD/trademind-data 2>/dev/null || true
$SUDO chmod 755 /extSSD/trademind-data

echo ""
echo "============================================"
echo "目录结构创建完成"
echo "============================================"
echo ""
echo "系统盘 (/opt/trademind):"
find /opt/trademind -type d | head -20

echo ""
echo "外置SSD (/extSSD/trademind-data):"
find /extSSD/trademind-data -type d | head -10

echo ""
echo "磁盘使用情况:"
df -h | grep -E "(/opt|/extSSD)" || df -h
echo ""
echo "下一步: Phase 2 - Docker 安装"
