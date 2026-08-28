# TradeMind AI Quant Lab - 离线部署包清单

## 重要说明

由于您的 AGX Xavier **无法直接联网**，必须通过 Windows 主节点下载所有依赖后传输到 Xavier。

**设备信息确认：**
- 设备: NVIDIA Jetson AGX Xavier Industrial
- RAM: 32GB Unified Memory
- 系统盘: /dev/root 27GB (已用 13GB, 剩余 13GB)
- 外置SSD: /dev/sda2 480GB (挂载 /extSSD)
- IP: 10.10.249.201
- **无法联网**

---

## 第一步：Windows主节点下载（在能上网的Windows机器上执行）

### 1.1 下载 Docker ARM64 版本

打开 PowerShell，执行以下命令下载：

```powershell
# 创建下载目录
mkdir C:\TradeMind-Deploy\downloads

cd C:\TradeMind-Deploy\downloads

# 下载 Docker 24.0.7 ARM64 二进制文件 (已编译版本)
# 地址: https://download.docker.com/linux/static/stable/aarch64/
# 下载: docker-24.0.7.tgz

# 使用浏览器下载：
# https://download.docker.com/linux/static/stable/aarch64/docker-24.0.7.tgz

# 下载 docker-compose 1.29.2 (Python版本，兼容性好)
# https://github.com/docker/compose/releases/download/1.29.2/docker-compose-Linux-aarch64
```

### 1.2 下载 NVIDIA Docker 支持

```powershell
# 下载 nvidia-container-toolkit
# 需要找 Jetson 专用版本
# 或者使用 JetPack 自带的 nvidia-docker2

# 下载地址 (NVIDIA 开发者中心需要登录):
# https://developer.nvidia.com/jetpack-archive
# 下载 JetPack 对应版本的 nvidia-docker2 deb 包
```

### 1.3 拉取 Docker 镜像（需要一台 Linux ARM64 机器，或树莓派）

**重要**：x86 Windows **无法直接拉取 ARM64 镜像**！

**解决方案：**
1. 使用另一台 Raspberry Pi 或 ARM64 Linux 机器拉取镜像
2. 或使用 Docker Desktop for Windows 的 QEMU 模拟 (较慢)
3. 或找一台 ARM64 云服务器临时拉取

**需要的镜像清单：**

```bash
# 基础镜像
python:3.10-slim-bookworm

# 消息队列 (轻量版，非management)
rabbitmq:3.12-alpine

# 缓存
redis:7-alpine

# 监控
prom/node-exporter:latest
prom/prometheus:latest (可选)

# 存储到 tar 文件
docker save python:3.10-slim-bookworm > python-3.10.tar
docker save rabbitmq:3.12-alpine > rabbitmq-3.12.tar
docker save redis:7-alpine > redis-7.tar
docker save prom/node-exporter:latest > node-exporter.tar
```

### 1.4 下载 Python 离线包

在 Linux ARM64 机器上执行：

```bash
# 创建虚拟环境
python3 -m venv /tmp/trademind-venv
source /tmp/trademind-venv/bin/activate

# 安装所需包
pip install --no-cache-dir \
    numpy==1.24.3 \
    pandas==2.0.3 \
    polars==0.18.15 \
    scipy==1.11.1 \
    scikit-learn==1.3.0 \
    numba==0.57.1 \
    fastapi==0.103.1 \
    uvicorn==0.23.2 \
    requests==2.31.0 \
    pyyaml==6.0.1 \
    schedule==1.2.0 \
    apscheduler==3.10.4 \
    websockets==11.0.3 \
    pika==1.3.2 \
    redis==5.0.0 \
    prometheus-client==0.17.1 \
    psutil==5.9.5

# 导出 requirements
cd /tmp/trademind-venv/lib/python3.*/site-packages

# 打包所有包
tar czf /tmp/python-packages.tar.gz .

# 或者下载 whl 文件
mkdir /tmp/whl-packages
pip download --no-deps -d /tmp/whl-packages \
    numpy==1.24.3 pandas==2.0.3 polars==0.18.15 \
    scipy==1.11.1 scikit-learn==1.3.0 numba==0.57.1 \
    fastapi==0.103.1 uvicorn==0.23.2 requests==2.31.0 \
    pyyaml==6.0.1 schedule==1.2.0 apscheduler==3.10.4 \
    websockets==11.0.3 pika==1.3.2 redis==5.0.0 \
    prometheus-client==0.17.1 psutil==5.9.5

tar czf /tmp/whl-packages.tar.gz -C /tmp/whl-packages .
```

### 1.5 TA-Lib 编译 (最复杂部分)

TA-Lib 需要从源码编译 ARM64 版本：

```bash
# 下载源码
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=/usr
make
make install

# 打包编译好的库
tar czf /tmp/ta-lib-arm64.tar.gz /usr/lib/libta_lib* /usr/include/ta-lib/
```

---

## 第二步：传输到 AGX Xavier

### 2.1 Windows 到 Xavier 传输

在 Windows PowerShell 中：

```powershell
# 设置 Xavier 信息
$XAVIER_IP = "10.10.249.201"
$XAVIER_USER = "dji"

# 传输文件
scp C:\TradeMind-Deploy\downloads\*.tar ${XAVIER_USER}@${XAVIER_IP}:/tmp/
scp C:\TradeMind-Deploy\downloads\*.tgz ${XAVIER_USER}@${XAVIER_IP}:/tmp/
scp C:\TradeMind-Deploy\downloads\*.deb ${XAVIER_USER}@${XAVIER_IP}:/tmp/

# 传输脚本
scp -r .\* ${XAVIER_USER}@${XAVIER_IP}:/tmp/trademind-deploy/
```

---

## 第三步：在 Xavier 上安装

等待我生成详细的安装脚本...

