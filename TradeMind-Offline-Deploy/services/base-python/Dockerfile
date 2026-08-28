# ============================================
# TradeMind 基础 Python 计算节点
# 适配: Jetson AGX Xavier Industrial ARM64
# Python: 3.10
# 功能: 量化计算基础环境
# ============================================

FROM python:3.10-slim-bookworm

LABEL maintainer="TradeMind AI Quant Lab"
LABEL version="1.0.0"
LABEL description="Base Python compute node for quantitative analysis"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random

# 系统级依赖 (轻量版本，用于编译)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    libomp-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 升级 pip 和基础工具
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 创建工作目录
WORKDIR /app

# 创建必要的子目录
RUN mkdir -p /app/{src,config,data,cache,logs}

# 设置 PYTHONPATH
ENV PYTHONPATH=/app:$PYTHONPATH

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# 默认命令
CMD ["python3"]
