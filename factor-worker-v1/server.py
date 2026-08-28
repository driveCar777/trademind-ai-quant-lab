#!/usr/bin/env python3
"""TradeMind Factor Worker v2.0 — Zero-dependency HTTP server.

Pure Python stdlib (http.server + json + hashlib + ThreadingMixIn).
No pip, no Docker, no third-party packages.
Designed for AGX Xavier bare-metal deployment (Python 3.6.9).

Port: 8080
Endpoints:
  GET  /health   — Health check
  POST /factor   — A-share multi-factor analysis (V2.0, ?v=1 for V1.0)
  GET  /factors  — List 15 supported factors
  GET  /stocks   — List all stocks in DB
  GET  /sectors  — List all sectors
"""

import hashlib
import json
import math
import sys
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

PORT = 8080
SERVICE_NAME = "factor-worker"
VERSION = "2.0.0"
WORKER_ID = "xavier-worker-02"
_start_time = datetime.utcnow()


# ═══════════════════════════════════════════════════════════════════════
#  STOCK DATABASE — 50 stocks across 12 sectors
# ═══════════════════════════════════════════════════════════════════════

_STOCKS = {
    # ── 白酒 (5) ──
    "600519": {"name": "贵州茅台", "roe": 30.12, "roa": 12.45, "pe": 28.5, "pb": 10.2, "ps": 9.1,  "div_yield": 1.20, "mc": 22000, "sector": "白酒", "rev_growth": 16.8, "profit_growth": 18.2, "roe_3y": 29.5, "debt_ratio": 22.1, "current_ratio": 3.8, "mom_60d": 5.3,  "vol_60d": 18.2, "vol_ratio": 1.10},
    "000858": {"name": "五粮液",   "roe": 25.80, "roa": 10.10, "pe": 22.3, "pb": 6.8,  "ps": 6.2,  "div_yield": 1.80, "mc": 5800,  "sector": "白酒", "rev_growth": 14.2, "profit_growth": 15.6, "roe_3y": 24.8, "debt_ratio": 25.3, "current_ratio": 3.2, "mom_60d": 3.1,  "vol_60d": 20.1, "vol_ratio": 1.05},
    "000568": {"name": "泸州老窖", "roe": 28.30, "roa": 11.50, "pe": 20.1, "pb": 8.5,  "ps": 7.8,  "div_yield": 2.10, "mc": 3200,  "sector": "白酒", "rev_growth": 18.5, "profit_growth": 20.1, "roe_3y": 27.2, "debt_ratio": 20.5, "current_ratio": 3.5, "mom_60d": 6.8,  "vol_60d": 22.3, "vol_ratio": 1.15},
    "002304": {"name": "洋河股份", "roe": 20.50, "roa": 9.80,  "pe": 16.8, "pb": 4.2,  "ps": 5.1,  "div_yield": 2.50, "mc": 2100,  "sector": "白酒", "rev_growth": 10.2, "profit_growth": 11.8, "roe_3y": 21.0, "debt_ratio": 28.7, "current_ratio": 2.8, "mom_60d": -1.2, "vol_60d": 19.5, "vol_ratio": 0.95},
    "603369": {"name": "今世缘",   "roe": 22.10, "roa": 10.80, "pe": 18.5, "pb": 5.1,  "ps": 5.8,  "div_yield": 1.90, "mc": 980,   "sector": "白酒", "rev_growth": 22.3, "profit_growth": 25.1, "roe_3y": 21.5, "debt_ratio": 24.1, "current_ratio": 3.0, "mom_60d": 8.2,  "vol_60d": 24.1, "vol_ratio": 1.20},

    # ── 银行 (5) ──
    "600036": {"name": "招商银行", "roe": 15.80, "roa": 0.95,  "pe": 6.5,  "pb": 1.0,  "ps": 2.8,  "div_yield": 4.20, "mc": 9200,  "sector": "银行", "rev_growth": 2.1,  "profit_growth": 3.5,  "roe_3y": 15.5, "debt_ratio": 92.1, "current_ratio": 0.0, "mom_60d": 2.1,  "vol_60d": 12.3, "vol_ratio": 0.90},
    "000001": {"name": "平安银行", "roe": 10.20, "roa": 0.65,  "pe": 5.8,  "pb": 0.6,  "ps": 1.5,  "div_yield": 5.10, "mc": 2200,  "sector": "银行", "rev_growth": -1.2, "profit_growth": 0.8,  "roe_3y": 10.0, "debt_ratio": 93.5, "current_ratio": 0.0, "mom_60d": -2.5, "vol_60d": 14.1, "vol_ratio": 0.85},
    "601166": {"name": "兴业银行", "roe": 12.30, "roa": 0.72,  "pe": 5.2,  "pb": 0.5,  "ps": 1.8,  "div_yield": 5.50, "mc": 3600,  "sector": "银行", "rev_growth": 1.5,  "profit_growth": 2.8,  "roe_3y": 12.1, "debt_ratio": 93.2, "current_ratio": 0.0, "mom_60d": 1.8,  "vol_60d": 13.5, "vol_ratio": 0.88},
    "601398": {"name": "工商银行", "roe": 11.50, "roa": 0.85,  "pe": 5.0,  "pb": 0.5,  "ps": 1.2,  "div_yield": 6.20, "mc": 18500, "sector": "银行", "rev_growth": 0.8,  "profit_growth": 1.5,  "roe_3y": 11.3, "debt_ratio": 91.8, "current_ratio": 0.0, "mom_60d": 0.5,  "vol_60d": 8.2,  "vol_ratio": 0.82},
    "601288": {"name": "农业银行", "roe": 10.80, "roa": 0.70,  "pe": 4.8,  "pb": 0.4,  "ps": 1.0,  "div_yield": 6.80, "mc": 12000, "sector": "银行", "rev_growth": 0.5,  "profit_growth": 1.2,  "roe_3y": 10.6, "debt_ratio": 92.5, "current_ratio": 0.0, "mom_60d": 0.2,  "vol_60d": 7.8,  "vol_ratio": 0.80},

    # ── 保险 (4) ──
    "601318": {"name": "中国平安", "roe": 16.50, "roa": 1.20,  "pe": 8.2,  "pb": 1.1,  "ps": 1.0,  "div_yield": 3.80, "mc": 4500,  "sector": "保险", "rev_growth": 5.2,  "profit_growth": 8.1,  "roe_3y": 16.0, "debt_ratio": 88.5, "current_ratio": 0.0, "mom_60d": 3.5,  "vol_60d": 16.2, "vol_ratio": 1.00},
    "601628": {"name": "中国人寿", "roe": 12.80, "roa": 0.80,  "pe": 10.5, "pb": 1.2,  "ps": 0.6,  "div_yield": 2.50, "mc": 5800,  "sector": "保险", "rev_growth": 3.8,  "profit_growth": 12.5, "roe_3y": 12.2, "debt_ratio": 90.1, "current_ratio": 0.0, "mom_60d": 4.2,  "vol_60d": 18.5, "vol_ratio": 1.05},
    "601601": {"name": "中国太保", "roe": 11.50, "roa": 0.90,  "pe": 9.8,  "pb": 1.0,  "ps": 0.7,  "div_yield": 3.20, "mc": 2800,  "sector": "保险", "rev_growth": 4.1,  "profit_growth": 6.8,  "roe_3y": 11.2, "debt_ratio": 89.5, "current_ratio": 0.0, "mom_60d": 2.8,  "vol_60d": 15.8, "vol_ratio": 0.95},
    "601336": {"name": "新华保险", "roe": 13.20, "roa": 0.85,  "pe": 7.5,  "pb": 0.9,  "ps": 0.5,  "div_yield": 3.50, "mc": 1500,  "sector": "保险", "rev_growth": 2.5,  "profit_growth": 10.2, "roe_3y": 12.8, "debt_ratio": 91.2, "current_ratio": 0.0, "mom_60d": 5.1,  "vol_60d": 17.2, "vol_ratio": 1.10},

    # ── 医药 (5) ──
    "600276": {"name": "恒瑞医药", "roe": 17.80, "roa": 11.20, "pe": 45.2, "pb": 8.7,  "ps": 12.5, "div_yield": 0.50, "mc": 2600,  "sector": "医药", "rev_growth": 12.5, "profit_growth": 15.2, "roe_3y": 18.0, "debt_ratio": 15.2, "current_ratio": 4.5, "mom_60d": -3.5, "vol_60d": 22.5, "vol_ratio": 1.15},
    "603259": {"name": "药明康德", "roe": 16.40, "roa": 9.50,  "pe": 22.8, "pb": 4.2,  "ps": 5.8,  "div_yield": 0.80, "mc": 1800,  "sector": "医药", "rev_growth": 8.5,  "profit_growth": 10.1, "roe_3y": 16.2, "debt_ratio": 32.1, "current_ratio": 2.5, "mom_60d": -5.2, "vol_60d": 25.8, "vol_ratio": 1.20},
    "000538": {"name": "云南白药", "roe": 15.20, "roa": 8.80,  "pe": 25.6, "pb": 3.8,  "ps": 4.2,  "div_yield": 1.50, "mc": 1050,  "sector": "医药", "rev_growth": 6.2,  "profit_growth": 8.5,  "roe_3y": 15.0, "debt_ratio": 28.5, "current_ratio": 2.8, "mom_60d": 1.2,  "vol_60d": 18.8, "vol_ratio": 1.00},
    "300015": {"name": "爱尔眼科", "roe": 18.50, "roa": 10.50, "pe": 38.5, "pb": 7.2,  "ps": 8.5,  "div_yield": 0.30, "mc": 1500,  "sector": "医药", "rev_growth": 20.1, "profit_growth": 22.5, "roe_3y": 17.8, "debt_ratio": 35.2, "current_ratio": 2.2, "mom_60d": -2.1, "vol_60d": 24.5, "vol_ratio": 1.05},
    "300760": {"name": "迈瑞医疗", "roe": 22.50, "roa": 13.80, "pe": 32.1, "pb": 9.5,  "ps": 10.2, "div_yield": 0.80, "mc": 3200,  "sector": "医药", "rev_growth": 18.2, "profit_growth": 20.8, "roe_3y": 22.0, "debt_ratio": 18.5, "current_ratio": 5.2, "mom_60d": 2.5,  "vol_60d": 20.1, "vol_ratio": 1.10},

    # ── 电子 (5) ──
    "002475": {"name": "立讯精密", "roe": 19.50, "roa": 8.20,  "pe": 18.2, "pb": 5.1,  "ps": 2.5,  "div_yield": 0.80, "mc": 2800,  "sector": "电子", "rev_growth": 15.8, "profit_growth": 18.5, "roe_3y": 18.8, "debt_ratio": 52.1, "current_ratio": 1.5, "mom_60d": 4.2,  "vol_60d": 22.8, "vol_ratio": 1.12},
    "002371": {"name": "北方华创", "roe": 14.80, "roa": 5.50,  "pe": 55.2, "pb": 8.8,  "ps": 12.1, "div_yield": 0.20, "mc": 1800,  "sector": "电子", "rev_growth": 35.2, "profit_growth": 42.1, "roe_3y": 13.5, "debt_ratio": 45.8, "current_ratio": 2.0, "mom_60d": 12.5, "vol_60d": 28.5, "vol_ratio": 1.25},
    "603986": {"name": "兆易创新", "roe": 16.20, "roa": 8.50,  "pe": 35.8, "pb": 6.2,  "ps": 8.5,  "div_yield": 0.40, "mc": 850,   "sector": "电子", "rev_growth": 22.5, "profit_growth": 28.2, "roe_3y": 15.5, "debt_ratio": 28.5, "current_ratio": 3.2, "mom_60d": 8.5,  "vol_60d": 30.2, "vol_ratio": 1.30},
    "600183": {"name": "生益科技", "roe": 14.50, "roa": 7.80,  "pe": 15.2, "pb": 2.8,  "ps": 2.2,  "div_yield": 2.20, "mc": 520,   "sector": "电子", "rev_growth": 12.8, "profit_growth": 15.5, "roe_3y": 14.0, "debt_ratio": 35.2, "current_ratio": 2.1, "mom_60d": 3.8,  "vol_60d": 20.5, "vol_ratio": 1.08},
    "300661": {"name": "圣邦股份", "roe": 20.80, "roa": 12.50, "pe": 62.5, "pb": 12.1, "ps": 18.5, "div_yield": 0.15, "mc": 680,   "sector": "电子", "rev_growth": 28.5, "profit_growth": 32.1, "roe_3y": 19.5, "debt_ratio": 12.8, "current_ratio": 5.8, "mom_60d": -1.5, "vol_60d": 32.5, "vol_ratio": 1.18},

    # ── 新能源 (5) ──
    "300750": {"name": "宁德时代", "roe": 22.80, "roa": 8.50,  "pe": 25.6, "pb": 7.5,  "ps": 4.8,  "div_yield": 0.50, "mc": 10500, "sector": "新能源", "rev_growth": 22.1, "profit_growth": 25.8, "roe_3y": 21.5, "debt_ratio": 62.5, "current_ratio": 1.2, "mom_60d": 6.5,  "vol_60d": 25.2, "vol_ratio": 1.15},
    "002594": {"name": "比亚迪",   "roe": 18.30, "roa": 5.20,  "pe": 20.1, "pb": 5.3,  "ps": 2.1,  "div_yield": 0.30, "mc": 7800,  "sector": "新能源", "rev_growth": 35.5, "profit_growth": 42.8, "roe_3y": 15.2, "debt_ratio": 72.1, "current_ratio": 1.0, "mom_60d": 8.8,  "vol_60d": 22.8, "vol_ratio": 1.20},
    "601012": {"name": "隆基绿能", "roe": 20.50, "roa": 6.80,  "pe": 15.3, "pb": 4.1,  "ps": 3.5,  "div_yield": 1.50, "mc": 2400,  "sector": "新能源", "rev_growth": -5.2, "profit_growth": -12.5, "roe_3y": 22.0, "debt_ratio": 55.8, "current_ratio": 1.5, "mom_60d": -8.5, "vol_60d": 28.5, "vol_ratio": 1.25},
    "600438": {"name": "通威股份", "roe": 25.10, "roa": 8.20,  "pe": 8.5,  "pb": 2.8,  "ps": 1.5,  "div_yield": 2.80, "mc": 1600,  "sector": "新能源", "rev_growth": -8.5, "profit_growth": -25.2, "roe_3y": 28.5, "debt_ratio": 58.2, "current_ratio": 1.3, "mom_60d": -12.1,"vol_60d": 32.5, "vol_ratio": 1.30},
    "002459": {"name": "晶澳科技", "roe": 18.80, "roa": 5.50,  "pe": 10.2, "pb": 2.5,  "ps": 1.2,  "div_yield": 1.80, "mc": 680,   "sector": "新能源", "rev_growth": -2.1, "profit_growth": -8.5, "roe_3y": 20.5, "debt_ratio": 65.2, "current_ratio": 1.1, "mom_60d": -6.2, "vol_60d": 30.1, "vol_ratio": 1.22},

    # ── 家电 (4) ──
    "000333": {"name": "美的集团", "roe": 22.30, "roa": 7.80,  "pe": 14.5, "pb": 3.8,  "ps": 1.8,  "div_yield": 2.80, "mc": 3600,  "sector": "家电", "rev_growth": 8.5,  "profit_growth": 12.2, "roe_3y": 21.5, "debt_ratio": 62.1, "current_ratio": 1.2, "mom_60d": 3.2,  "vol_60d": 16.5, "vol_ratio": 1.02},
    "000651": {"name": "格力电器", "roe": 25.50, "roa": 8.50,  "pe": 8.2,  "pb": 2.8,  "ps": 1.5,  "div_yield": 5.50, "mc": 2200,  "sector": "家电", "rev_growth": 3.2,  "profit_growth": 5.8,  "roe_3y": 24.8, "debt_ratio": 68.5, "current_ratio": 1.1, "mom_60d": 1.5,  "vol_60d": 18.2, "vol_ratio": 0.98},
    "002032": {"name": "苏泊尔",   "roe": 20.10, "roa": 10.20, "pe": 18.5, "pb": 5.5,  "ps": 3.2,  "div_yield": 1.80, "mc": 450,   "sector": "家电", "rev_growth": 6.8,  "profit_growth": 10.5, "roe_3y": 19.5, "debt_ratio": 38.2, "current_ratio": 2.0, "mom_60d": 2.1,  "vol_60d": 17.8, "vol_ratio": 1.00},
    "600690": {"name": "海尔智家", "roe": 18.50, "roa": 5.20,  "pe": 12.8, "pb": 2.5,  "ps": 1.2,  "div_yield": 3.20, "mc": 2800,  "sector": "家电", "rev_growth": 7.5,  "profit_growth": 11.2, "roe_3y": 17.8, "debt_ratio": 65.5, "current_ratio": 1.1, "mom_60d": 4.5,  "vol_60d": 15.2, "vol_ratio": 1.05},

    # ── 消费 (5) ──
    "603288": {"name": "海天味业", "roe": 24.50, "roa": 15.20, "pe": 35.2, "pb": 8.5,  "ps": 8.8,  "div_yield": 0.80, "mc": 2200,  "sector": "消费", "rev_growth": 5.2,  "profit_growth": 6.8,  "roe_3y": 25.0, "debt_ratio": 18.2, "current_ratio": 4.5, "mom_60d": -2.8, "vol_60d": 18.5, "vol_ratio": 0.95},
    "002714": {"name": "牧原股份", "roe": 18.70, "roa": 6.50,  "pe": 12.1, "pb": 3.2,  "ps": 3.8,  "div_yield": 1.20, "mc": 2800,  "sector": "消费", "rev_growth": 15.5, "profit_growth": 45.2, "roe_3y": 15.2, "debt_ratio": 55.8, "current_ratio": 1.3, "mom_60d": 10.5, "vol_60d": 28.2, "vol_ratio": 1.25},
    "600436": {"name": "片仔癀",   "roe": 22.80, "roa": 14.50, "pe": 55.8, "pb": 12.5, "ps": 18.2, "div_yield": 0.40, "mc": 1500,  "sector": "消费", "rev_growth": 12.8, "profit_growth": 15.5, "roe_3y": 22.2, "debt_ratio": 12.5, "current_ratio": 5.8, "mom_60d": -5.5, "vol_60d": 25.8, "vol_ratio": 1.12},
    "603517": {"name": "绝味食品", "roe": 16.50, "roa": 8.80,  "pe": 22.5, "pb": 4.2,  "ps": 3.5,  "div_yield": 1.50, "mc": 350,   "sector": "消费", "rev_growth": 10.2, "profit_growth": 12.8, "roe_3y": 16.0, "debt_ratio": 35.2, "current_ratio": 2.2, "mom_60d": -1.2, "vol_60d": 22.5, "vol_ratio": 1.08},
    "300146": {"name": "汤臣倍健", "roe": 15.80, "roa": 9.50,  "pe": 18.2, "pb": 3.5,  "ps": 4.2,  "div_yield": 1.80, "mc": 320,   "sector": "消费", "rev_growth": 8.5,  "profit_growth": 10.2, "roe_3y": 15.5, "debt_ratio": 28.5, "current_ratio": 2.8, "mom_60d": 1.8,  "vol_60d": 20.2, "vol_ratio": 1.02},

    # ── 矿业 (4) ──
    "601899": {"name": "紫金矿业", "roe": 21.40, "roa": 8.50,  "pe": 11.8, "pb": 3.5,  "ps": 2.2,  "div_yield": 2.50, "mc": 3200,  "sector": "矿业", "rev_growth": 18.5, "profit_growth": 22.8, "roe_3y": 18.5, "debt_ratio": 52.5, "current_ratio": 1.5, "mom_60d": 8.2,  "vol_60d": 22.5, "vol_ratio": 1.15},
    "600362": {"name": "江西铜业", "roe": 12.50, "roa": 4.80,  "pe": 8.5,  "pb": 1.5,  "ps": 0.3,  "div_yield": 3.80, "mc": 850,   "sector": "矿业", "rev_growth": 8.2,  "profit_growth": 12.5, "roe_3y": 11.8, "debt_ratio": 58.5, "current_ratio": 1.2, "mom_60d": 5.5,  "vol_60d": 20.5, "vol_ratio": 1.10},
    "601225": {"name": "陕西煤业", "roe": 22.50, "roa": 10.20, "pe": 7.5,  "pb": 2.2,  "ps": 2.8,  "div_yield": 5.80, "mc": 2200,  "sector": "矿业", "rev_growth": 5.5,  "profit_growth": 8.2,  "roe_3y": 21.5, "debt_ratio": 42.1, "current_ratio": 1.8, "mom_60d": 3.2,  "vol_60d": 16.8, "vol_ratio": 0.95},
    "000630": {"name": "铜陵有色", "roe": 8.50,  "roa": 3.20,  "pe": 12.5, "pb": 1.2,  "ps": 0.4,  "div_yield": 2.20, "mc": 380,   "sector": "矿业", "rev_growth": 6.2,  "profit_growth": 15.8, "roe_3y": 7.8,  "debt_ratio": 62.5, "current_ratio": 1.0, "mom_60d": 7.5,  "vol_60d": 25.2, "vol_ratio": 1.18},

    # ── 电力 (4) ──
    "600900": {"name": "长江电力", "roe": 16.20, "roa": 5.80,  "pe": 19.8, "pb": 3.0,  "ps": 6.5,  "div_yield": 3.50, "mc": 5500,  "sector": "电力", "rev_growth": 2.5,  "profit_growth": 5.2,  "roe_3y": 15.8, "debt_ratio": 62.5, "current_ratio": 0.8, "mom_60d": 1.2,  "vol_60d": 8.5,  "vol_ratio": 0.85},
    "600886": {"name": "国投电力", "roe": 14.50, "roa": 4.20,  "pe": 12.5, "pb": 2.2,  "ps": 2.8,  "div_yield": 3.80, "mc": 1200,  "sector": "电力", "rev_growth": 5.8,  "profit_growth": 12.2, "roe_3y": 13.8, "debt_ratio": 68.5, "current_ratio": 0.7, "mom_60d": 2.8,  "vol_60d": 12.5, "vol_ratio": 0.92},
    "003816": {"name": "中国广核", "roe": 10.80, "roa": 3.50,  "pe": 15.2, "pb": 1.8,  "ps": 3.2,  "div_yield": 3.20, "mc": 1800,  "sector": "电力", "rev_growth": 3.2,  "profit_growth": 5.8,  "roe_3y": 10.5, "debt_ratio": 58.2, "current_ratio": 0.9, "mom_60d": 0.8,  "vol_60d": 10.2, "vol_ratio": 0.88},
    "600905": {"name": "三峡能源", "roe": 8.50,  "roa": 2.80,  "pe": 18.5, "pb": 1.5,  "ps": 4.5,  "div_yield": 1.50, "mc": 1500,  "sector": "电力", "rev_growth": 12.5, "profit_growth": 15.8, "roe_3y": 7.8,  "debt_ratio": 65.2, "current_ratio": 0.8, "mom_60d": -1.5, "vol_60d": 15.8, "vol_ratio": 1.05},

    # ── 科技 (4) ──
    "002230": {"name": "科大讯飞", "roe": 8.50,  "roa": 3.80,  "pe": 85.2, "pb": 6.5,  "ps": 8.2,  "div_yield": 0.20, "mc": 1100,  "sector": "科技", "rev_growth": 18.5, "profit_growth": -5.2, "roe_3y": 7.5,  "debt_ratio": 42.5, "current_ratio": 1.8, "mom_60d": 5.2,  "vol_60d": 30.5, "vol_ratio": 1.22},
    "688981": {"name": "中芯国际", "roe": 6.20,  "roa": 2.50,  "pe": 42.5, "pb": 2.2,  "ps": 5.8,  "div_yield": 0.10, "mc": 2200,  "sector": "科技", "rev_growth": 12.2, "profit_growth": 25.8, "roe_3y": 5.5,  "debt_ratio": 38.5, "current_ratio": 2.2, "mom_60d": 8.5,  "vol_60d": 28.2, "vol_ratio": 1.18},
    "603501": {"name": "韦尔股份", "roe": 12.50, "roa": 5.80,  "pe": 28.5, "pb": 4.5,  "ps": 5.2,  "div_yield": 0.30, "mc": 1500,  "sector": "科技", "rev_growth": 22.8, "profit_growth": 35.2, "roe_3y": 11.2, "debt_ratio": 42.1, "current_ratio": 2.0, "mom_60d": 10.2, "vol_60d": 28.5, "vol_ratio": 1.15},
    "688036": {"name": "传音控股", "roe": 25.80, "roa": 10.50, "pe": 12.5, "pb": 4.8,  "ps": 1.2,  "div_yield": 1.50, "mc": 680,   "sector": "科技", "rev_growth": 28.5, "profit_growth": 32.8, "roe_3y": 22.5, "debt_ratio": 45.8, "current_ratio": 1.8, "mom_60d": 12.8, "vol_60d": 25.8, "vol_ratio": 1.20},

    # ── 其他 (4) ──
    "000002": {"name": "万科A",    "roe": 9.80,  "roa": 1.80,  "pe": 6.5,  "pb": 0.5,  "ps": 0.4,  "div_yield": 5.80, "mc": 1200,  "sector": "其他", "rev_growth": -15.2, "profit_growth": -25.8, "roe_3y": 12.5, "debt_ratio": 82.5, "current_ratio": 1.1, "mom_60d": -8.5, "vol_60d": 28.5, "vol_ratio": 1.25},
    "600048": {"name": "保利发展", "roe": 12.50, "roa": 2.20,  "pe": 5.2,  "pb": 0.6,  "ps": 0.3,  "div_yield": 6.20, "mc": 1800,  "sector": "其他", "rev_growth": -8.5, "profit_growth": -12.2, "roe_3y": 14.2, "debt_ratio": 78.5, "current_ratio": 1.2, "mom_60d": -3.2, "vol_60d": 22.5, "vol_ratio": 1.15},
    "601668": {"name": "中国建筑", "roe": 12.80, "roa": 2.50,  "pe": 4.5,  "pb": 0.5,  "ps": 0.2,  "div_yield": 5.50, "mc": 2200,  "sector": "其他", "rev_growth": 2.5,  "profit_growth": 3.8,  "roe_3y": 12.5, "debt_ratio": 75.2, "current_ratio": 1.1, "mom_60d": 1.5,  "vol_60d": 12.8, "vol_ratio": 0.90},
    "601319": {"name": "中国人保", "roe": 11.20, "roa": 1.50,  "pe": 8.5,  "pb": 0.8,  "ps": 0.5,  "div_yield": 4.20, "mc": 2200,  "sector": "其他", "rev_growth": 3.5,  "profit_growth": 8.2,  "roe_3y": 10.8, "debt_ratio": 85.2, "current_ratio": 0.0, "mom_60d": 2.2,  "vol_60d": 14.5, "vol_ratio": 0.92},
}

SECTORS = {}
for _code, _info in _STOCKS.items():
    _s = _info["sector"]
    if _s not in SECTORS:
        SECTORS[_s] = []
    SECTORS[_s].append(_code)


# ═══════════════════════════════════════════════════════════════════════
#  DETERMINISTIC RANDOM (hash-based, Python 3.6 safe)
# ═══════════════════════════════════════════════════════════════════════

def _seed(s):
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF

def _rand_range(seed_str, lo, hi):
    return lo + _seed(seed_str) * (hi - lo)

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ═══════════════════════════════════════════════════════════════════════
#  15 FACTOR COMPUTATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def _f_roe(fund, date):
    base = fund.get("roe", 15.0)
    v = _rand_range(fund["name"] + ":" + date + ":roe", -2.0, 2.0)
    return round(base + v, 2)

def _f_roa(fund, date):
    base = fund.get("roa", 5.0)
    v = _rand_range(fund["name"] + ":" + date + ":roa", -0.8, 0.8)
    return round(base + v, 2)

def _f_pe(fund, date):
    base = fund.get("pe", 15.0)
    v = _rand_range(fund["name"] + ":" + date + ":pe", -1.5, 1.5)
    return round(max(0.5, base + v), 2)

def _f_pb(fund, date):
    base = fund.get("pb", 2.0)
    v = _rand_range(fund["name"] + ":" + date + ":pb", -0.3, 0.3)
    return round(max(0.1, base + v), 2)

def _f_ps(fund, date):
    base = fund.get("ps", 3.0)
    v = _rand_range(fund["name"] + ":" + date + ":ps", -0.5, 0.5)
    return round(max(0.1, base + v), 2)

def _f_div_yield(fund, date):
    base = fund.get("div_yield", 1.5)
    v = _rand_range(fund["name"] + ":" + date + ":div", -0.3, 0.3)
    return round(max(0.0, base + v), 2)

def _f_mc(fund, date):
    base = fund.get("mc", 1000)
    v = _rand_range(fund["name"] + ":" + date + ":mc", -50, 50)
    return round(max(50, base + v), 0)

def _f_rev_growth(fund, date):
    base = fund.get("rev_growth", 10.0)
    v = _rand_range(fund["name"] + ":" + date + ":rg", -3.0, 3.0)
    return round(base + v, 2)

def _f_profit_growth(fund, date):
    base = fund.get("profit_growth", 10.0)
    v = _rand_range(fund["name"] + ":" + date + ":pg", -5.0, 5.0)
    return round(base + v, 2)

def _f_roe_3y(fund, date):
    base = fund.get("roe_3y", 15.0)
    v = _rand_range(fund["name"] + ":" + date + ":r3y", -1.0, 1.0)
    return round(base + v, 2)

def _f_debt_ratio(fund, date):
    base = fund.get("debt_ratio", 50.0)
    v = _rand_range(fund["name"] + ":" + date + ":dr", -2.0, 2.0)
    return round(_clamp(base + v, 5.0, 98.0), 2)

def _f_current_ratio(fund, date):
    base = fund.get("current_ratio", 1.5)
    if base == 0.0:
        return 0.0
    v = _rand_range(fund["name"] + ":" + date + ":cr", -0.2, 0.2)
    return round(max(0.1, base + v), 2)

def _f_mom_60d(fund, date):
    base = fund.get("mom_60d", 0.0)
    v = _rand_range(fund["name"] + ":" + date + ":mom", -3.0, 3.0)
    return round(base + v, 2)

def _f_vol_60d(fund, date):
    base = fund.get("vol_60d", 20.0)
    v = _rand_range(fund["name"] + ":" + date + ":vol", -2.0, 2.0)
    return round(max(3.0, base + v), 2)

def _f_vol_ratio(fund, date):
    base = fund.get("vol_ratio", 1.0)
    v = _rand_range(fund["name"] + ":" + date + ":vr", -0.1, 0.1)
    return round(max(0.3, base + v), 2)

FACTOR_FUNCS = {
    "roe": _f_roe,
    "roa": _f_roa,
    "pe": _f_pe,
    "pb": _f_pb,
    "ps": _f_ps,
    "dividend_yield": _f_div_yield,
    "market_cap_bn": _f_mc,
    "revenue_growth": _f_rev_growth,
    "profit_growth": _f_profit_growth,
    "roe_3y_avg": _f_roe_3y,
    "debt_ratio": _f_debt_ratio,
    "current_ratio": _f_current_ratio,
    "momentum_60d": _f_mom_60d,
    "volatility_60d": _f_vol_60d,
    "volume_ratio": _f_vol_ratio,
}


def _compute_all_factors(fund, date):
    factors = {
        "name": fund["name"],
        "sector": fund["sector"],
    }
    for key, func in FACTOR_FUNCS.items():
        factors[key] = func(fund, date)
    return factors


# ═══════════════════════════════════════════════════════════════════════
#  FIVE-DIMENSION SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════

def _score_value(factors):
    """价值维度 (25分): PE低→高分, PB低→高分, PS低→高分, 股息率高→高分"""
    pe = factors.get("pe", 15)
    pb = factors.get("pb", 3)
    ps = factors.get("ps", 3)
    div_y = factors.get("dividend_yield", 1.5)
    pe_score = _clamp(25 - pe * 0.6, 0, 25)
    pb_score = _clamp(15 - pb * 1.2, 0, 15)
    ps_score = _clamp(10 - ps * 1.0, 0, 10)
    div_score = _clamp(div_y * 3, 0, 15)
    return round(min(25, (pe_score + pb_score + ps_score + div_score) * 25 / 60), 1)


def _score_quality(factors):
    """质量维度 (25分): ROE高→高分, ROA高→高分, 3年ROE稳定→高分"""
    roe = factors.get("roe", 15)
    roa = factors.get("roa", 5)
    roe_3y = factors.get("roe_3y_avg", 15)
    roe_score = _clamp(roe * 0.8, 0, 15)
    roa_score = _clamp(roa * 1.2, 0, 10)
    stability = 10 - abs(roe - roe_3y) * 0.5
    stability = _clamp(stability, 0, 10)
    return round(min(25, (roe_score + roa_score + stability) * 25 / 35), 1)


def _score_momentum(factors):
    """动量维度 (20分): 利润增速高→高分, 60日正动量→高分"""
    pg = factors.get("profit_growth", 10)
    mom = factors.get("momentum_60d", 0)
    pg_score = _clamp(pg * 0.5, -5, 15)
    mom_score = _clamp(mom * 1.0 + 5, 0, 15)
    return round(min(20, max(0, (pg_score + mom_score) * 20 / 30)), 1)


def _score_risk(factors):
    """风险维度 (15分): 负债率低→高分, 流动比率高→高分, 波动率低→高分"""
    dr = factors.get("debt_ratio", 50)
    cr = factors.get("current_ratio", 1.5)
    vol = factors.get("volatility_60d", 20)
    dr_score = _clamp((100 - dr) * 0.15, 0, 8)
    cr_score = _clamp(cr * 2, 0, 5)
    vol_score = _clamp((35 - vol) * 0.3, 0, 7)
    return round(min(15, (dr_score + cr_score + vol_score) * 15 / 20), 1)


def _score_liquidity(factors):
    """流动性维度 (15分): 量比适中→高分, 大市值流动性好→高分"""
    vr = factors.get("volume_ratio", 1.0)
    mc = factors.get("market_cap_bn", 1000)
    if 0.8 <= vr <= 1.5:
        vr_score = 10
    elif vr < 0.8:
        vr_score = max(0, vr * 10)
    else:
        vr_score = max(0, 15 - vr * 5)
    mc_score = _clamp(math.log10(max(100, mc)) * 2 - 4, 0, 10)
    return round(min(15, (vr_score + mc_score) * 15 / 20), 1)


def _grade(total):
    if total >= 85: return "S"
    if total >= 70: return "A"
    if total >= 55: return "B"
    if total >= 40: return "C"
    return "D"


def _compute_score_v2(factors):
    dims = {
        "value": _score_value(factors),
        "quality": _score_quality(factors),
        "momentum": _score_momentum(factors),
        "risk": _score_risk(factors),
        "liquidity": _score_liquidity(factors),
    }
    total = round(dims["value"] + dims["quality"] + dims["momentum"] + dims["risk"] + dims["liquidity"], 1)
    total = _clamp(total, 0, 100)
    return total, dims


# ═══════════════════════════════════════════════════════════════════════
#  SECTOR RANK + PERCENTILE
# ═══════════════════════════════════════════════════════════════════════

def _compute_ranks_and_percentiles(stock_code, factors, all_scores):
    """Compute market-wide and sector rank + percentiles."""
    sector = factors["sector"]
    sector_scores = [(c, s) for c, s in all_scores.items()
                     if _STOCKS.get(c, {}).get("sector") == sector]
    sector_scores.sort(key=lambda x: x[1], reverse=True)
    market_sorted = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
    total = len(market_sorted)
    sector_total = len(sector_scores)

    market_rank = next((i + 1 for i, (c, _) in enumerate(market_sorted) if c == stock_code), total)
    sector_rank = next((i + 1 for i, (c, _) in enumerate(sector_scores) if c == stock_code), sector_total)

    def pct(rank, n):
        return round((1 - (rank - 1) / max(1, n)) * 100) if n > 0 else 50

    return {
        "rank_market": market_rank,
        "rank_sector": sector_rank,
        "total_stocks": total,
        "sector_stocks": sector_total,
    }, {
        "market": pct(market_rank, total),
        "sector": pct(sector_rank, sector_total),
    }


def _compute_all_scores():
    """Pre-compute scores for all stocks (needed for ranking)."""
    scores = {}
    for code, fund in _STOCKS.items():
        factors = _compute_all_factors(fund, "ranking")
        total, _ = _compute_score_v2(factors)
        scores[code] = total
    return scores


# ═══════════════════════════════════════════════════════════════════════
#  V1.0 COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════

def _compute_v1(fund, stock, date):
    seed = stock + ":" + date
    roe_base = fund.get("roe", 15.0)
    roe = round(roe_base + _rand_range(seed + ":roe", -2.0, 2.0), 2)
    pe = fund.get("pe", 15)
    pb = fund.get("pb", 2)
    mc = fund.get("mc", 1000)
    value = _clamp(50 - pe * 1.2 - pb * 1.5, 0, 50)
    quality = _clamp(roe * 0.9, 0, 30)
    size = 10 if 2000 < mc < 8000 else 5
    trend_b = int(_rand_range(seed + ":trend", 0, 10))
    score = _clamp(int(value + quality + size + trend_b), 0, 100)
    return {
        "roe": roe, "pe": pe, "pb": pb,
        "market_cap_bn": mc,
        "sector": fund.get("sector", "unknown"),
        "name": fund.get("name", ""),
        "value_score": round(value, 1),
        "quality_score": round(quality, 1),
        "momentum": round(_rand_range(seed + ":mom", -5, 5), 2),
        "volatility": round(_rand_range(seed + ":vol", 0.5, 5.5), 2),
        "liquidity_score": round(_rand_range(seed + ":liq", 0, 100), 1),
    }, score, bool(score >= 50)


# ═══════════════════════════════════════════════════════════════════════
#  HTTP HANDLER
# ═══════════════════════════════════════════════════════════════════════

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class FactorHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        sys.stderr.write("[%s] %s\n" % (ts, fmt % args))

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            now = datetime.utcnow()
            self._send_json({
                "status": "healthy",
                "service": SERVICE_NAME,
                "version": VERSION,
                "worker_id": WORKER_ID,
                "stock_count": len(_STOCKS),
                "sector_count": len(SECTORS),
                "uptime_seconds": round((now - _start_time).total_seconds(), 3),
                "timestamp": now.isoformat(),
            })

        elif path == "/factors":
            self._send_json({
                "factors": list(FACTOR_FUNCS.keys()),
                "dimensions": ["value", "quality", "momentum", "risk", "liquidity"],
                "version": VERSION,
                "total": len(FACTOR_FUNCS),
            })

        elif path == "/stocks":
            stocks = []
            for code in sorted(_STOCKS.keys()):
                f = _STOCKS[code]
                stocks.append({"code": code, "name": f["name"], "sector": f["sector"]})
            self._send_json({"stocks": stocks, "count": len(stocks)})

        elif path == "/sectors":
            result = {}
            for s, codes in sorted(SECTORS.items()):
                result[s] = {"count": len(codes), "stocks": codes}
            self._send_json({"sectors": result, "count": len(SECTORS)})

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/factor":
            try:
                body = self._read_body()
            except Exception:
                self._send_json({"error": "Invalid JSON"}, 400)
                return

            stock = body.get("stock", "")
            date = body.get("date", "")
            if not stock or not date:
                self._send_json({"error": "Missing 'stock' or 'date'"}, 400)
                return
            if len(stock) != 6 or len(date) != 8:
                self._send_json({"error": "Invalid stock code or date format"}, 400)
                return

            t0 = time.perf_counter()
            fund = _STOCKS.get(stock)
            v1_mode = body.get("v") == "1"

            if fund is None:
                fund = {
                    "name": "Stock-" + stock,
                    "roe": 12.0 + _rand_range(stock + ":roe", 0, 15),
                    "roa": 4.0 + _rand_range(stock + ":roa", 0, 8),
                    "pe": 10 + _rand_range(stock + ":pe", 0, 25),
                    "pb": 1 + _rand_range(stock + ":pb", 0, 6),
                    "ps": 1 + _rand_range(stock + ":ps", 0, 5),
                    "div_yield": _rand_range(stock + ":dy", 0, 3),
                    "mc": 1000 + int(_rand_range(stock + ":mc", 0, 8000)),
                    "sector": "未知",
                    "rev_growth": _rand_range(stock + ":rg", -10, 30),
                    "profit_growth": _rand_range(stock + ":pg", -15, 40),
                    "roe_3y": 10 + _rand_range(stock + ":r3y", 0, 15),
                    "debt_ratio": 30 + _rand_range(stock + ":dr", 0, 40),
                    "current_ratio": 0.5 + _rand_range(stock + ":cr", 0, 3),
                    "mom_60d": _rand_range(stock + ":mom", -15, 15),
                    "vol_60d": 15 + _rand_range(stock + ":vol", 0, 20),
                    "vol_ratio": 0.5 + _rand_range(stock + ":vr", 0, 1),
                }

            if v1_mode:
                factors, score, trend = _compute_v1(fund, stock, date)
                elapsed = (time.perf_counter() - t0) * 1000
                self._send_json({
                    "success": True,
                    "stock": stock,
                    "date": date,
                    "score": score,
                    "roe": factors.get("roe", 0),
                    "trend": trend,
                    "factors": factors,
                    "calculation_time_ms": round(elapsed, 3),
                    "timestamp": datetime.utcnow().isoformat(),
                })
                return

            # V2.0 mode
            factors = _compute_all_factors(fund, date)
            total_score, dims = _compute_score_v2(factors)

            all_scores = _compute_all_scores()
            all_scores[stock] = total_score
            ranks, pct = _compute_ranks_and_percentiles(stock, factors, all_scores)
            grade = _grade(total_score)

            elapsed = (time.perf_counter() - t0) * 1000
            self._send_json({
                "success": True,
                "stock": stock,
                "date": date,
                "version": VERSION,
                "score": {
                    "total": total_score,
                    "value": dims["value"],
                    "quality": dims["quality"],
                    "momentum": dims["momentum"],
                    "risk": dims["risk"],
                    "liquidity": dims["liquidity"],
                    "grade": grade,
                    "rank_market": ranks["rank_market"],
                    "rank_sector": ranks["rank_sector"],
                    "total_stocks": ranks["total_stocks"],
                    "sector_stocks": ranks["sector_stocks"],
                },
                "factors": factors,
                "percentiles": {
                    "market": {"score": pct["market"]},
                    "sector": {"score": pct["sector"]},
                },
                "calculation_time_ms": round(elapsed, 3),
                "timestamp": datetime.utcnow().isoformat(),
            })
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    server = ThreadedHTTPServer(("0.0.0.0", PORT), FactorHandler)
    print("=" * 60)
    print("  TradeMind Factor Worker v%s" % VERSION)
    print("  Worker ID: %s" % WORKER_ID)
    print("  Port: %d" % PORT)
    print("  Stock DB: %d stocks, %d sectors" % (len(_STOCKS), len(SECTORS)))
    print("  Factors: %d (5-dimension scoring)" % len(FACTOR_FUNCS))
    print("  Python: %s" % sys.version.split()[0])
    print("  Started: %s" % datetime.now().isoformat())
    print("=" * 60)
    print("  Endpoints:")
    print("    GET  http://0.0.0.0:%d/health" % PORT)
    print("    GET  http://0.0.0.0:%d/factors" % PORT)
    print("    GET  http://0.0.0.0:%d/stocks" % PORT)
    print("    GET  http://0.0.0.0:%d/sectors" % PORT)
    print("    POST http://0.0.0.0:%d/factor" % PORT)
    print("=" * 60)
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
