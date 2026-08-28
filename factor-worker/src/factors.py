#!/usr/bin/env python3
"""
Multi-Factor Calculator for TradeMind
Supports alpha factors, risk factors, and fundamental factors
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import numba
from numba import jit


class FactorType(Enum):
    """Supported factor types"""
    # Alpha Factors
    MOMENTUM = "momentum"
    REVERSAL = "reversal"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    VALUE = "value"
    QUALITY = "quality"
    GROWTH = "growth"
    SIZE = "size"
    
    # Risk Factors
    BETA = "beta"
    ALPHA = "alpha"
    RESIDUAL_VOLATILITY = "residual_volatility"
    DRAWDOWN = "drawdown"
    
    # Technical Factors
    PRICE_MOMENTUM = "price_momentum"
    VOLUME_MOMENTUM = "volume_momentum"
    PRICE_ACCELERATION = "price_acceleration"
    
    # Statistical Factors
    SKEWNESS = "skewness"
    KURTOSIS = "kurtosis"
    AUTOCORRELATION = "autocorrelation"
    
    # Composite Factors
    COMPOSITE_MOMENTUM = "composite_momentum"
    COMPOSITE_VALUE = "composite_value"
    COMPOSITE_QUALITY = "composite_quality"


@dataclass
class FactorConfig:
    """Configuration for factor calculation"""
    lookback_period: int = 252
    smoothing_period: int = 20
    benchmark_symbol: str = "^GSPC"
    risk_free_rate: float = 0.02


class FactorCalculator:
    """
    Multi-Factor Calculator for TradeMind
    Optimized for AGX Xavier with numba acceleration
    """
    
    def __init__(self):
        self.factors: Dict[FactorType, Callable] = {
            # Alpha Factors
            FactorType.MOMENTUM: self.calculate_momentum,
            FactorType.REVERSAL: self.calculate_reversal,
            FactorType.VOLATILITY: self.calculate_volatility_factor,
            FactorType.LIQUIDITY: self.calculate_liquidity,
            FactorType.VALUE: self.calculate_value,
            FactorType.QUALITY: self.calculate_quality,
            FactorType.GROWTH: self.calculate_growth,
            FactorType.SIZE: self.calculate_size,
            
            # Risk Factors
            FactorType.BETA: self.calculate_beta,
            FactorType.ALPHA: self.calculate_alpha,
            FactorType.RESIDUAL_VOLATILITY: self.calculate_residual_volatility,
            FactorType.DRAWDOWN: self.calculate_drawdown_factor,
            
            # Technical Factors
            FactorType.PRICE_MOMENTUM: self.calculate_price_momentum,
            FactorType.VOLUME_MOMENTUM: self.calculate_volume_momentum,
            FactorType.PRICE_ACCELERATION: self.calculate_price_acceleration,
            
            # Statistical Factors
            FactorType.SKEWNESS: self.calculate_skewness,
            FactorType.KURTOSIS: self.calculate_kurtosis,
            FactorType.AUTOCORRELATION: self.calculate_autocorrelation,
            
            # Composite Factors
            FactorType.COMPOSITE_MOMENTUM: self.calculate_composite_momentum,
            FactorType.COMPOSITE_VALUE: self.calculate_composite_value,
            FactorType.COMPOSITE_QUALITY: self.calculate_composite_quality,
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of supported factors"""
        return [f.value for f in self.factors.keys()]
    
    def calculate(self, data: pd.DataFrame, factor: str, 
                  lookback: int = 252,
                  config: Optional[FactorConfig] = None) -> Dict[str, Any]:
        """Calculate a single factor"""
        config = config or FactorConfig(lookback_period=lookback)
        
        # Validate data
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Find factor
        factor_type = None
        for f_type in FactorType:
            if f_type.value == factor.lower():
                factor_type = f_type
                break
        
        if factor_type is None:
            raise ValueError(f"Unknown factor: {factor}")
        
        calc_func = self.factors.get(factor_type)
        if calc_func:
            return calc_func(data, config)
        
        raise ValueError(f"Calculator not implemented for {factor}")
    
    # ==================== Alpha Factors ====================
    
    def calculate_momentum(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate momentum factor (12-month minus 1-month return)"""
        prices = data['close']
        
        # Calculate returns
        returns_12m = prices.pct_change(periods=config.lookback_period)
        returns_1m = prices.pct_change(periods=21)
        
        # Momentum = 12m return - 1m return (exclude most recent month)
        momentum = returns_12m - returns_1m
        
        return {
            'value': momentum.iloc[-1] if not momentum.empty else None,
            'rank': momentum.rank(pct=True).iloc[-1] if not momentum.empty else None,
            'zscore': ((momentum - momentum.mean()) / momentum.std()).iloc[-1] if not momentum.empty else None,
            'values': momentum.fillna(0).tolist()
        }
    
    def calculate_reversal(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate short-term reversal factor"""
        prices = data['close']
        
        # 1-month return as reversal indicator
        reversal = -prices.pct_change(periods=21)
        
        return {
            'value': reversal.iloc[-1] if not reversal.empty else None,
            'rank': reversal.rank(pct=True).iloc[-1] if not reversal.empty else None,
            'zscore': ((reversal - reversal.mean()) / reversal.std()).iloc[-1] if not reversal.empty else None,
            'values': reversal.fillna(0).tolist()
        }
    
    def calculate_volatility_factor(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate volatility factor (low volatility anomaly)"""
        returns = data['close'].pct_change()
        
        # Realized volatility
        vol = returns.rolling(window=config.lookback_period).std() * np.sqrt(252)
        
        # Low volatility is preferred (inverse)
        vol_factor = 1 / (vol + 1e-6)
        
        return {
            'value': vol_factor.iloc[-1] if not vol_factor.empty else None,
            'rank': vol_factor.rank(pct=True).iloc[-1] if not vol_factor.empty else None,
            'volatility': vol.iloc[-1] if not vol.empty else None,
            'values': vol_factor.fillna(0).tolist()
        }
    
    def calculate_liquidity(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate liquidity factor"""
        # Turnover rate
        avg_volume = data['volume'].rolling(window=21).mean()
        avg_price = data['close'].rolling(window=21).mean()
        turnover = avg_volume * avg_price
        
        # Low turnover (high liquidity) is preferred
        liquidity = 1 / (turnover + 1e-6)
        
        return {
            'value': liquidity.iloc[-1] if not liquidity.empty else None,
            'rank': liquidity.rank(pct=True).iloc[-1] if not liquidity.empty else None,
            'turnover': turnover.iloc[-1] if not turnover.empty else None,
            'values': liquidity.fillna(0).tolist()
        }
    
    def calculate_value(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate value factor (inverse P/E proxy using price momentum)"""
        prices = data['close']
        
        # Price-to-moving-average ratio as value proxy
        sma_200 = prices.rolling(window=200).mean()
        value_ratio = sma_200 / prices
        
        return {
            'value': value_ratio.iloc[-1] if not value_ratio.empty else None,
            'rank': value_ratio.rank(pct=True).iloc[-1] if not value_ratio.empty else None,
            'zscore': ((value_ratio - value_ratio.mean()) / value_ratio.std()).iloc[-1] if not value_ratio.empty else None,
            'values': value_ratio.fillna(0).tolist()
        }
    
    def calculate_quality(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate quality factor (earnings stability)"""
        returns = data['close'].pct_change()
        
        # Consistency of returns (inverse of volatility)
        consistency = 1 / (returns.rolling(window=config.lookback_period).std() + 1e-6)
        
        return {
            'value': consistency.iloc[-1] if not consistency.empty else None,
            'rank': consistency.rank(pct=True).iloc[-1] if not consistency.empty else None,
            'values': consistency.fillna(0).tolist()
        }
    
    def calculate_growth(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate growth factor (price trend acceleration)"""
        prices = data['close']
        
        # Price growth rate
        sma_20 = prices.rolling(window=20).mean()
        sma_60 = prices.rolling(window=60).mean()
        
        growth_rate = (sma_20 - sma_60) / sma_60
        
        return {
            'value': growth_rate.iloc[-1] if not growth_rate.empty else None,
            'rank': growth_rate.rank(pct=True).iloc[-1] if not growth_rate.empty else None,
            'zscore': ((growth_rate - growth_rate.mean()) / growth_rate.std()).iloc[-1] if not growth_rate.empty else None,
            'values': growth_rate.fillna(0).tolist()
        }
    
    def calculate_size(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate size factor (inverse market cap proxy)"""
        # Use volume * price as proxy for market cap
        market_cap_proxy = data['volume'] * data['close']
        
        # Inverse (small cap preference)
        size_factor = 1 / (market_cap_proxy + 1e-6)
        
        return {
            'value': size_factor.iloc[-1] if not size_factor.empty else None,
            'rank': size_factor.rank(pct=True).iloc[-1] if not size_factor.empty else None,
            'values': size_factor.fillna(0).tolist()
        }
    
    # ==================== Risk Factors ====================
    
    def calculate_beta(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate beta factor (market sensitivity)"""
        returns = data['close'].pct_change().dropna()
        
        # Use price return as proxy for market
        market_returns = returns.copy()
        
        if len(returns) < config.lookback_period:
            config.lookback_period = len(returns)
        
        # Calculate rolling beta
        rolling_window = min(config.lookback_period, len(returns) // 2)
        
        betas = []
        for i in range(rolling_window, len(returns)):
            stock_ret = returns.iloc[i-rolling_window:i].values.reshape(-1, 1)
            market_ret = market_returns.iloc[i-rolling_window:i].values.reshape(-1, 1)
            
            if len(stock_ret) > 1 and len(market_ret) > 1:
                try:
                    reg = LinearRegression().fit(market_ret, stock_ret)
                    betas.append(reg.coef_[0][0])
                except:
                    betas.append(1.0)
        
        beta_value = betas[-1] if betas else 1.0
        
        return {
            'value': beta_value,
            'mean': np.mean(betas) if betas else 1.0,
            'std': np.std(betas) if betas else 0.0,
            'values': betas
        }
    
    def calculate_alpha(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate alpha factor (excess return)"""
        returns = data['close'].pct_change().dropna()
        
        # Daily risk-free rate
        daily_rf = config.risk_free_rate / 252
        
        # Excess return over risk-free rate
        excess_returns = returns - daily_rf
        
        # Rolling alpha (mean excess return)
        alpha = excess_returns.rolling(window=config.lookback_period).mean() * 252
        
        return {
            'value': alpha.iloc[-1] if not alpha.empty else None,
            'annualized': alpha.iloc[-1] if not alpha.empty else None,
            'values': alpha.fillna(0).tolist()
        }
    
    def calculate_residual_volatility(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate residual volatility (unexplained volatility)"""
        returns = data['close'].pct_change().dropna()
        
        # Market returns proxy
        market_returns = returns.copy()
        
        # Calculate residuals
        rolling_window = min(config.lookback_period, len(returns) // 2)
        
        residual_vols = []
        for i in range(rolling_window, len(returns)):
            stock_ret = returns.iloc[i-rolling_window:i]
            market_ret = market_returns.iloc[i-rolling_window:i]
            
            # Simple regression
            if len(stock_ret) > 1:
                try:
                    beta = np.corrcoef(stock_ret, market_ret)[0, 1] * np.std(stock_ret) / np.std(market_ret)
                    predicted = beta * market_ret
                    residuals = stock_ret - predicted
                    residual_vol = np.std(residuals) * np.sqrt(252)
                    residual_vols.append(residual_vol)
                except:
                    residual_vols.append(0.0)
        
        return {
            'value': residual_vols[-1] if residual_vols else 0.0,
            'mean': np.mean(residual_vols) if residual_vols else 0.0,
            'values': residual_vols
        }
    
    def calculate_drawdown_factor(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate drawdown-based risk factor"""
        prices = data['close']
        
        # Calculate drawdowns
        rolling_max = prices.rolling(window=config.lookback_period, min_periods=1).max()
        drawdown = (prices - rolling_max) / rolling_max
        
        # Max drawdown
        max_dd = drawdown.min()
        
        # Calmar ratio (return / max drawdown)
        returns = prices.pct_change(periods=config.lookback_period).iloc[-1]
        calmar = returns / abs(max_dd) if max_dd != 0 else 0
        
        return {
            'value': max_dd,
            'max_drawdown': max_dd,
            'calmar_ratio': calmar,
            'avg_drawdown': drawdown.mean(),
            'values': drawdown.fillna(0).tolist()
        }
    
    # ==================== Technical Factors ====================
    
    def calculate_price_momentum(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate price momentum factor"""
        close = data['close']
        
        # Multiple timeframe momentum
        mom_1m = (close / close.shift(21) - 1)
        mom_3m = (close / close.shift(63) - 1)
        mom_6m = (close / close.shift(126) - 1)
        
        # Combined momentum
        combined = 0.4 * mom_1m + 0.3 * mom_3m + 0.3 * mom_6m
        
        return {
            'value': combined.iloc[-1] if not combined.empty else None,
            'mom_1m': mom_1m.iloc[-1] if not mom_1m.empty else None,
            'mom_3m': mom_3m.iloc[-1] if not mom_3m.empty else None,
            'mom_6m': mom_6m.iloc[-1] if not mom_6m.empty else None,
            'values': combined.fillna(0).tolist()
        }
    
    def calculate_volume_momentum(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate volume momentum factor"""
        volume = data['volume']
        
        # Volume trend
        vol_sma_20 = volume.rolling(window=20).mean()
        vol_sma_60 = volume.rolling(window=60).mean()
        
        vol_momentum = (vol_sma_20 - vol_sma_60) / vol_sma_60
        
        return {
            'value': vol_momentum.iloc[-1] if not vol_momentum.empty else None,
            'trend': 'increasing' if (vol_momentum.iloc[-1] > 0 if not vol_momentum.empty else False) else 'decreasing',
            'values': vol_momentum.fillna(0).tolist()
        }
    
    def calculate_price_acceleration(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate price acceleration (second derivative)"""
        prices = data['close']
        
        # First derivative (velocity)
        velocity = prices.diff()
        
        # Second derivative (acceleration)
        acceleration = velocity.diff()
        
        # Normalize
        normalized_accel = acceleration / prices * 100
        
        return {
            'value': normalized_accel.iloc[-1] if not normalized_accel.empty else None,
            'acceleration': acceleration.iloc[-1] if not acceleration.empty else None,
            'direction': 'up' if (normalized_accel.iloc[-1] > 0 if not normalized_accel.empty else False) else 'down',
            'values': normalized_accel.fillna(0).tolist()
        }
    
    # ==================== Statistical Factors ====================
    
    def calculate_skewness(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate return skewness"""
        returns = data['close'].pct_change().dropna()
        
        # Rolling skewness
        skew = returns.rolling(window=config.lookback_period).skew()
        
        return {
            'value': skew.iloc[-1] if not skew.empty else None,
            'mean': skew.mean() if not skew.empty else None,
            'bias': 'positive' if (skew.iloc[-1] > 0 if not skew.empty else False) else 'negative',
            'values': skew.fillna(0).tolist()
        }
    
    def calculate_kurtosis(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate return kurtosis"""
        returns = data['close'].pct_change().dropna()
        
        # Rolling kurtosis
        kurt = returns.rolling(window=config.lookback_period).kurt()
        
        return {
            'value': kurt.iloc[-1] if not kurt.empty else None,
            'mean': kurt.mean() if not kurt.empty else None,
            'fat_tails': kurt.iloc[-1] > 3 if not kurt.empty else False,
            'values': kurt.fillna(0).tolist()
        }
    
    def calculate_autocorrelation(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate return autocorrelation"""
        returns = data['close'].pct_change().dropna()
        
        # Lag-1 autocorrelation
        autocorr = returns.rolling(window=config.lookback_period).apply(
            lambda x: x.autocorr(lag=1), raw=False
        )
        
        return {
            'value': autocorr.iloc[-1] if not autocorr.empty else None,
            'mean': autocorr.mean() if not autocorr.empty else None,
            'predictable': abs(autocorr.iloc[-1]) > 0.1 if not autocorr.empty else False,
            'values': autocorr.fillna(0).tolist()
        }
    
    # ==================== Composite Factors ====================
    
    def calculate_composite_momentum(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate composite momentum factor"""
        # Combine multiple momentum signals
        price_mom = self.calculate_price_momentum(data, config)
        vol_mom = self.calculate_volume_momentum(data, config)
        
        # Weighted combination
        composite = 0.7 * price_mom.get('value', 0) + 0.3 * vol_mom.get('value', 0)
        
        return {
            'value': composite,
            'components': {
                'price_momentum': price_mom.get('value'),
                'volume_momentum': vol_mom.get('value')
            },
            'rank': None,  # Would require cross-sectional comparison
            'values': []
        }
    
    def calculate_composite_value(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate composite value factor"""
        value = self.calculate_value(data, config)
        size = self.calculate_size(data, config)
        
        composite = 0.6 * value.get('value', 0) + 0.4 * size.get('value', 0)
        
        return {
            'value': composite,
            'components': {
                'value': value.get('value'),
                'size': size.get('value')
            },
            'rank': None,
            'values': []
        }
    
    def calculate_composite_quality(self, data: pd.DataFrame, config: FactorConfig) -> Dict[str, Any]:
        """Calculate composite quality factor"""
        quality = self.calculate_quality(data, config)
        volatility = self.calculate_volatility_factor(data, config)
        
        composite = 0.5 * quality.get('value', 0) + 0.5 * volatility.get('value', 0)
        
        return {
            'value': composite,
            'components': {
                'quality': quality.get('value'),
                'stability': volatility.get('value')
            },
            'rank': None,
            'values': []
        }
