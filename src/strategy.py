"""
Trading Strategy Engine - Core strategy logic separated from data and plotting
Focuses purely on trade signals and position management
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import json


@dataclass
class Trade:
    """Trade data structure"""
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    return_pct: Optional[float] = None
    exit_reason: Optional[str] = None
    position_size: float = 1.0
    
    def to_dict(self) -> Dict:
        """Convert trade to dictionary"""
        return asdict(self)


@dataclass
class Position:
    """Current position data structure"""
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    entry_date: datetime
    size: float = 1.0
    unrealized_pnl: float = 0.0


class RiskManager:
    """Risk management for trading strategies"""
    
    def __init__(self, take_profit: float = 0.02, stop_loss: float = 0.01, 
                 max_position_size: float = 1.0):
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.max_position_size = max_position_size
    
    def should_take_profit(self, position: Position, current_price: float) -> bool:
        """Check if position should be closed for take profit"""
        if position.side == 'long':
            return_pct = (current_price - position.entry_price) / position.entry_price
            return return_pct >= self.take_profit
        else:  # short
            return_pct = (position.entry_price - current_price) / position.entry_price
            return return_pct >= self.take_profit
    
    def should_stop_loss(self, position: Position, current_price: float) -> bool:
        """Check if position should be closed for stop loss"""
        if position.side == 'long':
            return_pct = (current_price - position.entry_price) / position.entry_price
            return return_pct <= -self.stop_loss
        else:  # short
            return_pct = (position.entry_price - current_price) / position.entry_price
            return return_pct <= -self.stop_loss
    
    def calculate_return(self, position: Position, exit_price: float) -> float:
        """Calculate return percentage for a position"""
        if position.side == 'long':
            return (exit_price - position.entry_price) / position.entry_price
        else:  # short
            return (position.entry_price - exit_price) / position.entry_price


class BaseStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, symbol: str, risk_manager: RiskManager = None):
        self.symbol = symbol
        self.risk_manager = risk_manager or RiskManager()
        self.current_position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.on_trade_callback: Optional[Callable] = None
        self.on_position_callback: Optional[Callable] = None
    
    def set_trade_callback(self, callback: Callable) -> None:
        """Set callback for when trades are executed"""
        self.on_trade_callback = callback
    
    def set_position_callback(self, callback: Callable) -> None:
        """Set callback for position updates"""
        self.on_position_callback = callback
    
    def generate_signals(self, data: pd.DataFrame, indicators: Dict) -> pd.Series:
        """Generate trading signals - to be implemented by subclasses"""
        raise NotImplementedError
    
    def enter_position(self, side: str, price: float, date: datetime, size: float = 1.0) -> None:
        """Enter a new position"""
        if self.current_position is not None:
            print(f"Warning: Already in position, cannot enter new {side} position")
            return
        
        self.current_position = Position(
            symbol=self.symbol,
            side=side,
            entry_price=price,
            entry_date=date,
            size=size
        )
        
        if self.on_position_callback:
            self.on_position_callback(self.current_position)
    
    def exit_position(self, price: float, date: datetime, reason: str) -> Optional[Trade]:
        """Exit current position"""
        if self.current_position is None:
            return None
        
        return_pct = self.risk_manager.calculate_return(self.current_position, price)
        
        trade = Trade(
            entry_date=self.current_position.entry_date,
            entry_price=self.current_position.entry_price,
            exit_date=date,
            exit_price=price,
            return_pct=return_pct,
            exit_reason=reason,
            position_size=self.current_position.size
        )
        
        self.trades.append(trade)
        self.current_position = None
        
        if self.on_trade_callback:
            self.on_trade_callback(trade)
        
        return trade
    
    def update_position(self, current_price: float, current_date: datetime) -> Optional[Trade]:
        """Update current position and check for exit conditions"""
        if self.current_position is None:
            return None
        
        # Update unrealized PnL
        self.current_position.unrealized_pnl = self.risk_manager.calculate_return(
            self.current_position, current_price
        )
        
        # Check exit conditions
        if self.risk_manager.should_take_profit(self.current_position, current_price):
            return self.exit_position(current_price, current_date, "Take Profit")
        elif self.risk_manager.should_stop_loss(self.current_position, current_price):
            return self.exit_position(current_price, current_date, "Stop Loss")
        
        return None
    
    def backtest(self, data: pd.DataFrame, indicators: Dict) -> List[Trade]:
        """Run backtest on historical data"""
        signals = self.generate_signals(data, indicators)
        
        for i in range(len(data)):
            current_date = data.index[i]
            current_price = float(data['Close'].iloc[i])
            current_signal = bool(signals.iloc[i]) if not pd.isna(signals.iloc[i]) else False
            
            # Update existing position
            trade = self.update_position(current_price, current_date)
            
            # Check for new entry signals
            if self.current_position is None and current_signal:
                self.enter_position('long', current_price, current_date)
        
        # Close any remaining position at the end
        if self.current_position is not None:
            final_price = float(data['Close'].iloc[-1])
            final_date = data.index[-1]
            self.exit_position(final_price, final_date, "End of Period")
        
        return self.trades
    
    def calculate_performance(self) -> Dict[str, Any]:
        """Calculate strategy performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'average_return': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        returns = [trade.return_pct for trade in self.trades]
        winning_trades = [r for r in returns if r > 0]
        losing_trades = [r for r in returns if r <= 0]
        
        # Calculate cumulative returns for drawdown
        cumulative_returns = np.cumprod([1 + r for r in returns])
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0
        
        # Sharpe ratio (simplified - assuming daily returns)
        mean_return = np.mean(returns) if returns else 0
        std_return = np.std(returns) if len(returns) > 1 else 0
        sharpe_ratio = mean_return / std_return if std_return > 0 else 0
        
        performance = {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trades) * 100,
            'total_return': sum(returns) * 100,
            'average_return': mean_return * 100,
            'best_trade': max(returns) * 100 if returns else 0,
            'worst_trade': min(returns) * 100 if returns else 0,
            'sharpe_ratio': sharpe_ratio * np.sqrt(252),  # Annualized
            'max_drawdown': max_drawdown * 100,
            'take_profit_hits': len([t for t in self.trades if t.exit_reason == 'Take Profit']),
            'stop_loss_hits': len([t for t in self.trades if t.exit_reason == 'Stop Loss'])
        }
        
        return performance


class MACDStrategy(BaseStrategy):
    """MACD Crossover Strategy Implementation with 200 EMA Trend Filter"""
    
    def __init__(self, symbol: str, risk_manager: RiskManager = None):
        super().__init__(symbol, risk_manager)
        self.strategy_name = "MACD Crossover + 200 EMA Filter"
    
    def generate_signals(self, data: pd.DataFrame, indicators: Dict) -> pd.Series:
        """Generate MACD crossover signals with 200 EMA trend filter"""
        macd_data = indicators.get('MACD', {})
        ema_200_data = indicators.get('EMA_200', {})
        
        if not macd_data:
            return pd.Series([False] * len(data), index=data.index)
        
        # MACD crossover above signal line while both below zero
        macd_cross = (
            (macd_data['MACD'] > macd_data['Signal']) & 
            (macd_data['MACD_prev'] <= macd_data['Signal_prev']) &
            (macd_data['MACD'] < 0) &
            (macd_data['Signal'] < 0)
        )
        
        # 200 EMA trend filter - only trade when price is above 200 EMA
        if ema_200_data and 'EMA_200' in ema_200_data:
            price_above_ema200 = data['Close'] > ema_200_data['EMA_200']
            # Combine MACD signal with EMA filter
            bullish_cross = macd_cross & price_above_ema200
        else:
            # Fallback to MACD only if 200 EMA not available
            print("Warning: 200 EMA not available, using MACD signals only")
            bullish_cross = macd_cross
        
        return bullish_cross


class StrategyEngine:
    """Main engine that coordinates strategy execution"""
    
    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy
        self.real_time_mode = False
        self.data_buffer = []
        
    def run_backtest(self, data: pd.DataFrame, indicators: Dict) -> Dict[str, Any]:
        """Run historical backtest"""
        print(f"Running backtest for {self.strategy.symbol} using {self.strategy.strategy_name}")
        
        trades = self.strategy.backtest(data, indicators)
        performance = self.strategy.calculate_performance()
        
        return {
            'trades': [trade.to_dict() for trade in trades],
            'performance': performance,
            'strategy_name': self.strategy.strategy_name,
            'symbol': self.strategy.symbol
        }
    
    def start_real_time_trading(self) -> None:
        """Start real-time strategy execution"""
        self.real_time_mode = True
        print(f"Started real-time trading for {self.strategy.symbol}")
    
    def stop_real_time_trading(self) -> None:
        """Stop real-time strategy execution"""
        self.real_time_mode = False
        print(f"Stopped real-time trading for {self.strategy.symbol}")
    
    def process_real_time_data(self, candle_data: Dict, indicators: Dict) -> None:
        """Process incoming real-time data"""
        if not self.real_time_mode:
            return
        
        # Convert candle data to DataFrame row for signal generation
        # This is a simplified version - in practice you'd maintain a rolling window
        current_price = candle_data['Close']
        current_date = candle_data['timestamp']
        
        # Update existing position
        if self.strategy.current_position:
            trade = self.strategy.update_position(current_price, current_date)
            if trade:
                print(f"Position closed: {trade.exit_reason} at {current_price}")
        
        # Check for new signals (you'd need to implement signal generation for real-time)
        # This would require maintaining a rolling window of recent data
    
    def export_results_json(self) -> str:
        """Export strategy results as JSON for frontend"""
        trades = [trade.to_dict() for trade in self.strategy.trades]
        performance = self.strategy.calculate_performance()
        
        result = {
            'strategy_name': self.strategy.strategy_name,
            'symbol': self.strategy.symbol,
            'trades': trades,
            'performance': performance,
            'current_position': self.strategy.current_position.to_dict() if self.strategy.current_position else None,
            'timestamp': datetime.now().isoformat()
        }
        
        return json.dumps(result, default=str)
