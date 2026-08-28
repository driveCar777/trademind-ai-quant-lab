#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TradeMind Indicator Worker - Compatible with Python 3.6"""

import os
import sys
import json
import logging
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import redis
from fastapi import FastAPI
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('indicator-worker')

# Initialize FastAPI
app = FastAPI(title="TradeMind Indicator Worker")

# Initialize Redis connection
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

def calc_sma(prices: List[float], period: int = 20) -> List[float]:
    """Calculate Simple Moving Average"""
    s = pd.Series(prices)
    return s.rolling(window=period).mean().tolist()

def calc_ema(prices: List[float], period: int = 20) -> List[float]:
    """Calculate Exponential Moving Average"""
    s = pd.Series(prices)
    return s.ewm(span=period, adjust=False).mean().tolist()

def calc_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Any]:
    """Calculate MACD"""
    s = pd.Series(prices)
    ema_fast = s.ewm(span=fast, adjust=False).mean()
    ema_slow = s.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        'macd': macd_line.tolist(),
        'signal': signal_line.tolist(),
        'histogram': histogram.tolist()
    }

def calc_rsi(prices: List[float], period: int = 14) -> List[float]:
    """Calculate RSI"""
    s = pd.Series(prices)
    delta = s.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.tolist()

def calc_bollinger(prices: List[float], period: int = 20, std: int = 2) -> Dict[str, Any]:
    """Calculate Bollinger Bands"""
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
    """Health check endpoint"""
    status = {"status": "healthy", "worker": "indicator"}
    if redis_client:
        try:
            redis_client.ping()
            status["redis"] = "connected"
        except:
            status["redis"] = "disconnected"
    return status

@app.get("/")
def root():
    return {"service": "TradeMind Indicator Worker", "version": "1.0.0"}

@app.post("/calculate/{indicator}")
def calculate(indicator: str, data: Dict[str, Any]):
    """Calculate technical indicator"""
    prices = data.get('prices', [])
    if not prices:
        return {"error": "No prices provided"}
    
    params = data.get('params', {})
    
    if indicator == "sma":
        result = {"values": calc_sma(prices, params.get('period', 20))}
    elif indicator == "ema":
        result = {"values": calc_ema(prices, params.get('period', 20))}
    elif indicator == "macd":
        result = calc_macd(prices)
    elif indicator == "rsi":
        result = {"values": calc_rsi(prices, params.get('period', 14))}
    elif indicator == "boll":
        result = calc_bollinger(prices, params.get('period', 20), params.get('std', 2))
    else:
        return {"error": "Unknown indicator: {}".format(indicator)}
    
    return {"indicator": indicator, "result": result}

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
