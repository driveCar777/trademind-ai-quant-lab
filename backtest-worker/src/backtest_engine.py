#!/usr/bin/env python3
"""
Backtest Engine for TradeMind
Event-driven backtesting with realistic execution
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Order object"""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    timestamp: Optional[datetime] = None
    fill_price: Optional[float] = None
    fill_quantity: float = 0.0
    commission: float = 0.0


@dataclass
class Position:
    """Position object"""
    symbol: str
    quantity: float
    avg_price: float
    market_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.market_price
    
    @property
    def unrealized_pnl(self) -> float:
        return self.quantity * (self.market_price - self.avg_price)
    
    @property
    def weight(self, portfolio_value: float) -> float:
        return self.market_value / portfolio_value if portfolio_value > 0 else 0.0


@dataclass
class Trade:
    """Trade record"""
    timestamp: datetime
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float


class Strategy:
    """Base strategy class"""
    
    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
        self.data: Dict[str, pd.DataFrame] = {}
        self.current_time: Optional[datetime] = None
    
    def initialize(self, data: Dict[str, pd.DataFrame]):
        """Initialize with market data"""
        self.data = data
    
    def on_bar(self, time: datetime) -> List[Order]:
        """Process bar data and return orders"""
        self.current_time = time
        return []
    
    def get_price(self, symbol: str, time: datetime) -> float:
        """Get price for symbol at time"""
        if symbol in self.data:
            df = self.data[symbol]
            mask = df.index <= time
            if mask.any():
                return df[mask].iloc[-1]['close']
        return 0.0


class MovingAverageCrossStrategy(Strategy):
    """Moving average crossover strategy"""
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.fast_period = params.get('fast_period', 20)
        self.slow_period = params.get('slow_period', 50)
        self.position_size = params.get('position_size', 0.1)
        self.positions: Dict[str, float] = {}
    
    def on_bar(self, time: datetime) -> List[Order]:
        orders = []
        
        for symbol, df in self.data.items():
            # Get data up to current time
            mask = df.index <= time
            if not mask.any():
                continue
            
            data = df[mask]
            if len(data) < self.slow_period:
                continue
            
            # Calculate moving averages
            fast_ma = data['close'].rolling(self.fast_period).mean().iloc[-1]
            slow_ma = data['close'].rolling(self.slow_period).mean().iloc[-1]
            
            current_price = data['close'].iloc[-1]
            current_position = self.positions.get(symbol, 0)
            
            # Trading logic
            if fast_ma > slow_ma and current_position <= 0:
                # Buy signal
                order = Order(
                    id=f"{time}_{symbol}_buy",
                    symbol=symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=self.position_size,
                    timestamp=time
                )
                orders.append(order)
                self.positions[symbol] = self.position_size
                
            elif fast_ma < slow_ma and current_position > 0:
                # Sell signal
                order = Order(
                    id=f"{time}_{symbol}_sell",
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=current_position,
                    timestamp=time
                )
                orders.append(order)
                self.positions[symbol] = 0
        
        return orders


class BacktestEngine:
    """Event-driven backtest engine"""
    
    def __init__(self):
        self.cash: float = 0.0
        self.initial_capital: float = 0.0
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.commission_rate: float = 0.001
        self.slippage: float = 0.0005
        
    def run(self, data: Dict[str, pd.DataFrame],
            strategy_id: str,
            strategy_params: Dict[str, Any],
            initial_capital: float = 100000.0,
            commission: float = 0.001,
            slippage: float = 0.0005) -> Dict[str, Any]:
        """Run backtest"""
        
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission
        self.slippage = slippage
        
        # Initialize strategy
        strategy = self._create_strategy(strategy_id, strategy_params)
        strategy.initialize(data)
        
        # Get all timestamps
        timestamps = self._get_timestamps(data)
        
        # Run simulation
        for timestamp in timestamps:
            # Update positions with current prices
            self._update_positions(timestamp, data)
            
            # Get orders from strategy
            orders = strategy.on_bar(timestamp)
            
            # Execute orders
            for order in orders:
                self._execute_order(order, timestamp, data)
            
            # Record equity
            self._record_equity(timestamp)
        
        # Calculate performance metrics
        return self._calculate_performance()
    
    def _create_strategy(self, strategy_id: str, params: Dict[str, Any]) -> Strategy:
        """Create strategy instance"""
        strategies = {
            'ma_cross': MovingAverageCrossStrategy,
        }
        
        strategy_class = strategies.get(strategy_id, MovingAverageCrossStrategy)
        return strategy_class(params)
    
    def _get_timestamps(self, data: Dict[str, pd.DataFrame]) -> List[datetime]:
        """Get all unique timestamps from data"""
        timestamps = set()
        for df in data.values():
            timestamps.update(df.index)
        return sorted(timestamps)
    
    def _update_positions(self, timestamp: datetime, data: Dict[str, pd.DataFrame]):
        """Update position market prices"""
        for symbol, position in self.positions.items():
            if symbol in data:
                df = data[symbol]
                mask = df.index <= timestamp
                if mask.any():
                    position.market_price = df[mask].iloc[-1]['close']
    
    def _execute_order(self, order: Order, timestamp: datetime, data: Dict[str, pd.DataFrame]):
        """Execute an order"""
        if order.symbol not in data:
            order.status = OrderStatus.REJECTED
            return
        
        df = data[order.symbol]
        mask = df.index <= timestamp
        if not mask.any():
            order.status = OrderStatus.REJECTED
            return
        
        current_bar = df[mask].iloc[-1]
        
        # Get execution price with slippage
        if order.side == OrderSide.BUY:
            fill_price = current_bar['high'] * (1 + self.slippage)
        else:
            fill_price = current_bar['low'] * (1 - self.slippage)
        
        # Calculate commission
        trade_value = order.quantity * fill_price
        commission = trade_value * self.commission_rate
        
        # Update cash
        if order.side == OrderSide.BUY:
            cost = trade_value + commission
            if cost > self.cash:
                order.status = OrderStatus.REJECTED
                return
            self.cash -= cost
        else:
            proceeds = trade_value - commission
            self.cash += proceeds
        
        # Update position
        if order.symbol in self.positions:
            position = self.positions[order.symbol]
            if order.side == OrderSide.BUY:
                # Update average price
                total_value = position.quantity * position.avg_price + order.quantity * fill_price
                position.quantity += order.quantity
                position.avg_price = total_value / position.quantity
            else:
                position.quantity -= order.quantity
                if position.quantity <= 0:
                    del self.positions[order.symbol]
        else:
            if order.side == OrderSide.BUY:
                self.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    avg_price=fill_price,
                    market_price=fill_price
                )
        
        # Record trade
        order.status = OrderStatus.FILLED
        order.fill_price = fill_price
        order.fill_quantity = order.quantity
        order.commission = commission
        
        self.trades.append(Trade(
            timestamp=timestamp,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            commission=commission
        ))
        
        self.orders.append(order)
    
    def _record_equity(self, timestamp: datetime):
        """Record equity at timestamp"""
        positions_value = sum(p.market_value for p in self.positions.values())
        total_equity = self.cash + positions_value
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'positions_value': positions_value,
            'total_equity': total_equity,
            'num_positions': len(self.positions)
        })
    
    def _calculate_performance(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not self.equity_curve:
            return {'error': 'No equity data'}
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        # Calculate returns
        equity_df['returns'] = equity_df['total_equity'].pct_change()
        equity_df['cumulative_returns'] = (1 + equity_df['returns']).cumprod() - 1
        
        # Performance metrics
        total_return = (equity_df['total_equity'].iloc[-1] / self.initial_capital) - 1
        
        # Annualized metrics (assuming daily data)
        daily_returns = equity_df['returns'].dropna()
        annual_return = daily_returns.mean() * 252
        annual_volatility = daily_returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # Drawdown
        rolling_max = equity_df['total_equity'].cummax()
        drawdown = (equity_df['total_equity'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Win rate
        winning_trades = len([t for t in self.trades if t.side == OrderSide.SELL and t.price > 0])
        total_trades = len([t for t in self.trades if t.side == OrderSide.SELL])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Trade statistics
        trade_stats = {
            'total_trades': len(self.trades),
            'total_commission': sum(t.commission for t in self.trades),
            'avg_trade_size': np.mean([t.quantity for t in self.trades]) if self.trades else 0,
        }
        
        return {
            'total_return': total_return,
            'annualized_return': annual_return,
            'annualized_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'final_equity': equity_df['total_equity'].iloc[-1],
            'initial_capital': self.initial_capital,
            'trade_stats': trade_stats,
            'num_trades': len(self.orders),
            'equity_curve': equity_df['total_equity'].to_dict(),
            'positions': {s: {'quantity': p.quantity, 'avg_price': p.avg_price} 
                         for s, p in self.positions.items()}
        }
