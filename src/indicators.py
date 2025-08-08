"""
Indicators Module - Technical analysis indicators
Separated from strategy logic for reusability
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


class IndicatorCalculator:
    """Base class for technical indicators"""
    
    @staticmethod
    def validate_data(data: pd.DataFrame, required_columns: list) -> None:
        """Validate that required columns exist in the data"""
        missing_cols = [col for col in required_columns if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")


class MACDCalculator(IndicatorCalculator):
    """MACD (Moving Average Convergence Divergence) indicator calculator"""
    
    def __init__(self, fast_length: int = 12, slow_length: int = 26, 
                 signal_smoothing: int = 9, source: str = 'close', 
                 oscillator_ma_type: str = 'EMA', signal_line_ma_type: str = 'EMA'):
        self.fast_length = fast_length
        self.slow_length = slow_length
        self.signal_smoothing = signal_smoothing
        self.source = source.lower()
        self.oscillator_ma_type = oscillator_ma_type.upper()
        self.signal_line_ma_type = signal_line_ma_type.upper()
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        required_columns = ['Open', 'High', 'Low', 'Close']
        self.validate_data(data, required_columns)
        
        # Select source price
        if self.source == 'close':
            source_price = data['Close']
        elif self.source == 'high':
            source_price = data['High']
        elif self.source == 'low':
            source_price = data['Low']
        elif self.source == 'open':
            source_price = data['Open']
        else:
            source_price = data['Close']
        
        # Calculate EMAs (we'll implement SMA later if needed)
        if self.oscillator_ma_type == 'EMA':
            ema_fast = source_price.ewm(span=self.fast_length, adjust=False).mean()
            ema_slow = source_price.ewm(span=self.slow_length, adjust=False).mean()
        else:
            # Default to EMA for now
            ema_fast = source_price.ewm(span=self.fast_length, adjust=False).mean()
            ema_slow = source_price.ewm(span=self.slow_length, adjust=False).mean()
        
        # Calculate MACD line
        macd = ema_fast - ema_slow
        
        # Calculate Signal line
        if self.signal_line_ma_type == 'EMA':
            signal = macd.ewm(span=self.signal_smoothing, adjust=False).mean()
        else:
            # Default to EMA for now
            signal = macd.ewm(span=self.signal_smoothing, adjust=False).mean()
        
        # Calculate Histogram
        histogram = macd - signal
        
        return {
            'MACD': macd,
            'Signal': signal,
            'Histogram': histogram,
            'MACD_prev': macd.shift(1),
            'Signal_prev': signal.shift(1)
        }
    
    def get_crossover_signals(self, macd_data: Dict[str, pd.Series]) -> pd.Series:
        """Detect bullish MACD crossover signals"""
        bullish_cross = (
            (macd_data['MACD'] > macd_data['Signal']) & 
            (macd_data['MACD_prev'] <= macd_data['Signal_prev']) &
            (macd_data['MACD'] < 0) &
            (macd_data['Signal'] < 0)
        )
        
        return bullish_cross


class RSICalculator(IndicatorCalculator):
    """RSI (Relative Strength Index) indicator calculator"""
    
    def __init__(self, period: int = 14, source: str = 'close'):
        self.period = period
        self.source = source.lower()
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate RSI indicator"""
        required_columns = ['Close']
        self.validate_data(data, required_columns)
        
        # Select source price
        if self.source == 'close':
            source_price = data['Close']
        else:
            source_price = data['Close']  # Default to close
        
        # Calculate price changes
        delta = source_price.diff()
        
        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        # Calculate RSI
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return {
            'RSI': rsi,
            'RSI_Overbought': pd.Series([70] * len(rsi), index=rsi.index),
            'RSI_Oversold': pd.Series([30] * len(rsi), index=rsi.index)
        }


class MovingAverageCalculator(IndicatorCalculator):
    """Moving Average calculator (SMA, EMA, etc.)"""
    
    def __init__(self, period: int = 20, ma_type: str = 'SMA', source: str = 'close'):
        self.period = period
        self.ma_type = ma_type.upper()
        self.source = source.lower()
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate moving average"""
        required_columns = ['Close']
        self.validate_data(data, required_columns)
        
        # Select source price
        if self.source == 'close':
            source_price = data['Close']
        elif self.source == 'high':
            source_price = data['High']
        elif self.source == 'low':
            source_price = data['Low']
        elif self.source == 'open':
            source_price = data['Open']
        else:
            source_price = data['Close']
        
        if self.ma_type == 'SMA':
            ma = source_price.rolling(window=self.period).mean()
        elif self.ma_type == 'EMA':
            ma = source_price.ewm(span=self.period, adjust=False).mean()
        else:
            # Default to SMA
            ma = source_price.rolling(window=self.period).mean()
        
        return {
            f'{self.ma_type}_{self.period}': ma
        }


class IndicatorManager:
    """Manages multiple indicators and provides unified interface"""
    
    def __init__(self):
        self.indicators = {}
        self.results = {}
    
    def add_indicator(self, name: str, calculator: IndicatorCalculator) -> None:
        """Add an indicator calculator"""
        self.indicators[name] = calculator
    
    def calculate_all(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all registered indicators"""
        self.results = {}
        
        for name, calculator in self.indicators.items():
            try:
                self.results[name] = calculator.calculate(data)
            except Exception as e:
                print(f"Error calculating {name}: {e}")
                self.results[name] = {}
        
        return self.results
    
    def get_indicator_data(self, name: str) -> Dict[str, pd.Series]:
        """Get specific indicator data"""
        return self.results.get(name, {})
    
    def export_indicators_json(self) -> str:
        """Export indicator data as JSON for frontend"""
        import json
        
        export_data = {}
        
        for indicator_name, indicator_data in self.results.items():
            export_data[indicator_name] = {}
            
            for series_name, series_data in indicator_data.items():
                if isinstance(series_data, pd.Series):
                    # Convert NaN values to None for JSON serialization
                    values_list = series_data.tolist()
                    values_list = [None if pd.isna(x) else x for x in values_list]
                    
                    export_data[indicator_name][series_name] = {
                        'values': values_list,
                        'timestamps': series_data.index.astype(str).tolist()
                    }
        
        return json.dumps(export_data, default=str)
