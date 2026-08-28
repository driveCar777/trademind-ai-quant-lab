"""TradeMind Factor Worker v1.0 — A-Share Stock Factor Calculation.

Lightweight FastAPI service for A-share multi-factor analysis.
Designed for AGX Xavier deployment.
"""

import hashlib
import math
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ── App ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TradeMind Factor Worker",
    version="1.0.0",
    description="A-Share Stock Factor Calculation Worker",
)
_start_time = datetime.utcnow()

WORKER_ID = "xavier-worker-02"
SERVICE_NAME = "factor-worker"
VERSION = "1.0.0"


# ── Schemas ────────────────────────────────────────────────────────────

class FactorRequest(BaseModel):
    stock: str = Field(..., min_length=6, max_length=6, description="A-share stock code, e.g. 600519")
    date: str = Field(..., min_length=8, max_length=8, description="Date YYYYMMDD, e.g. 20260724")
    factors: Optional[List[str]] = Field(default=None, description="Specific factors to compute (all if None)")


class FactorResponse(BaseModel):
    success: bool = True
    stock: str
    date: str
    score: int
    roe: float
    trend: bool
    factors: Dict[str, Any]
    calculation_time_ms: float
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    worker_id: str
    uptime_seconds: float
    timestamp: datetime


# ── A-Share Factor Engine ──────────────────────────────────────────────

# Simulated fundamental data for well-known A-share stocks.
# In production, this comes from Tushare/Wind/EastMoney API.
_STOCK_FUNDAMENTALS = {
    "600519": {"name": "贵州茅台", "roe": 30.12, "pe": 28.5, "pb": 10.2, "market_cap": 22000, "sector": "白酒"},
    "000858": {"name": "五粮液",   "roe": 25.80, "pe": 22.3, "pb": 6.8,  "market_cap": 5800,  "sector": "白酒"},
    "601318": {"name": "中国平安", "roe": 16.50, "pe": 8.2,  "pb": 1.1,  "market_cap": 4500,  "sector": "保险"},
    "000333": {"name": "美的集团", "roe": 22.30, "pe": 14.5, "pb": 3.8,  "market_cap": 3600,  "sector": "家电"},
    "002714": {"name": "牧原股份", "roe": 18.70, "pe": 12.1, "pb": 3.2,  "market_cap": 2800,  "sector": "养殖"},
    "600036": {"name": "招商银行", "roe": 15.80, "pe": 6.5,  "pb": 1.0,  "market_cap": 9200,  "sector": "银行"},
    "000001": {"name": "平安银行", "roe": 10.20, "pe": 5.8,  "pb": 0.6,  "market_cap": 2200,  "sector": "银行"},
    "601012": {"name": "隆基绿能", "roe": 20.50, "pe": 15.3, "pb": 4.1,  "market_cap": 2400,  "sector": "光伏"},
    "300750": {"name": "宁德时代", "roe": 22.80, "pe": 25.6, "pb": 7.5,  "market_cap": 10500, "sector": "锂电"},
    "002594": {"name": "比亚迪",   "roe": 18.30, "pe": 20.1, "pb": 5.3,  "market_cap": 7800,  "sector": "汽车"},
    "601899": {"name": "紫金矿业", "roe": 21.40, "pe": 11.8, "pb": 3.5,  "market_cap": 3200,  "sector": "矿业"},
    "600900": {"name": "长江电力", "roe": 16.20, "pe": 19.8, "pb": 3.0,  "market_cap": 5500,  "sector": "电力"},
    "002475": {"name": "立讯精密", "roe": 19.50, "pe": 18.2, "pb": 5.1,  "market_cap": 2800,  "sector": "电子"},
    "600276": {"name": "恒瑞医药", "roe": 17.80, "pe": 45.2, "pb": 8.7,  "market_cap": 2600,  "sector": "医药"},
    "603259": {"name": "药明康德", "roe": 16.40, "pe": 22.8, "pb": 4.2,  "market_cap": 1800,  "sector": "CXO"},
}


def _deterministic_random(seed: str, field: str) -> float:
    """Generate a deterministic pseudo-random value from stock+date+field."""
    h = hashlib.sha256(f"{seed}:{field}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def compute_score(fund: dict, seed: str) -> int:
    """Composite factor score (0-100) based on fundamental factors."""
    roe = fund.get("roe", 15)
    pe = fund.get("pe", 15)
    pb = fund.get("pb", 2)
    mc = fund.get("market_cap", 1000)

    # Value factor: lower PE/PB is better
    value_score = max(0, min(50, int(50 - pe * 1.2 - pb * 1.5)))

    # Quality factor: higher ROE is better
    quality_score = max(0, min(30, int(roe * 0.9)))

    # Size factor: mid-cap bonus
    size_score = 10 if 2000 < mc < 8000 else 5

    # Trend: deterministic hash
    trend_bonus = int(_deterministic_random(seed, "trend") * 10)

    total = value_score + quality_score + size_score + trend_bonus
    return max(0, min(100, total))


def compute_roe(fund: dict, date: str) -> float:
    """Return ROE with slight date-dependent variation."""
    base = fund.get("roe", 15.0)
    variation = _deterministic_random(fund.get("name", ""), date) * 2 - 1  # -1 to +1
    return round(base + variation, 2)


def compute_trend(fund: dict, date: str) -> bool:
    """Determine trend direction (up/down)."""
    score = compute_score(fund, date)
    return score >= 50


def compute_all_factors(fund: dict, date: str) -> Dict[str, Any]:
    """Compute all individual factors."""
    seed = f"{fund.get('name', '')}:{date}"
    roe = compute_roe(fund, date)

    return {
        "roe": roe,
        "pe": fund.get("pe", 0),
        "pb": fund.get("pb", 0),
        "market_cap_bn": fund.get("market_cap", 0),
        "sector": fund.get("sector", "unknown"),
        "name": fund.get("name", "unknown"),
        "value_score": round(max(0, min(50, 50 - fund.get("pe", 15) * 1.2 - fund.get("pb", 2) * 1.5)), 1),
        "quality_score": round(max(0, min(30, roe * 0.9)), 1),
        "momentum": round(_deterministic_random(seed, "momentum") * 10 - 5, 2),
        "volatility": round(_deterministic_random(seed, "vol") * 5 + 0.5, 2),
        "liquidity_score": round(_deterministic_random(seed, "liq") * 100, 1),
    }


# ── Routes ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    now = datetime.utcnow()
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=VERSION,
        worker_id=WORKER_ID,
        uptime_seconds=round((now - _start_time).total_seconds(), 3),
        timestamp=now,
    )


@app.post("/factor", response_model=FactorResponse)
def calculate_factor(request: FactorRequest):
    start = time.perf_counter()

    stock = request.stock
    date = request.date

    # Validate date format
    try:
        datetime.strptime(date, "%Y%m%d")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date}. Expected YYYYMMDD.")

    # Look up stock fundamentals
    fund = _STOCK_FUNDAMENTALS.get(stock)
    if fund is None:
        # For unknown stocks, generate synthetic data
        fund = {
            "name": f"Stock-{stock}",
            "roe": 12.0 + _deterministic_random(stock, "roe_base") * 15,
            "pe": 10 + _deterministic_random(stock, "pe_base") * 25,
            "pb": 1 + _deterministic_random(stock, "pb_base") * 6,
            "market_cap": 1000 + int(_deterministic_random(stock, "mc") * 8000),
            "sector": "未知",
        }

    score = compute_score(fund, f"{stock}:{date}")
    roe = compute_roe(fund, date)
    trend = compute_trend(fund, date)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return FactorResponse(
        success=True,
        stock=stock,
        date=date,
        score=score,
        roe=roe,
        trend=trend,
        factors=compute_all_factors(fund, date),
        calculation_time_ms=round(elapsed_ms, 3),
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/factors")
def list_supported_factors():
    return {
        "factors": [
            "score", "roe", "pe", "pb", "market_cap_bn",
            "sector", "value_score", "quality_score",
            "momentum", "volatility", "liquidity_score",
        ],
        "description": "A-Share multi-factor analysis",
    }
