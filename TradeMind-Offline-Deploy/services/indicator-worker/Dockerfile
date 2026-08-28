# ============================================
# TradeMind Indicator Worker
# 技术指标计算服务
# 计算: EMA, MACD, RSI, ATR, ADX, BOLL
# ============================================

FROM trademind/base-python:v1.0

LABEL maintainer="TradeMind AI Quant Lab"
LABEL version="1.0.0"
LABEL description="Technical indicator calculation worker"

# 安装量化计算库
# 注意: 这些包需要离线准备
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 复制源代码
COPY src/ /app/src/

# 设置工作目录
WORKDIR /app

# 暴露健康检查端口
EXPOSE 8000

# 运行服务
CMD ["python3", "-m", "src.main"]
