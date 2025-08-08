"""
Data Provider - Handles all data fetching and real-time connections
Separates data concerns from strategy logic
"""

import pandas as pd
import numpy as np
from binance.client import Client
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Callable
import json

# Optional import for real-time streaming (not required for basic functionality)
try:
    from binance import ThreadedWebsocketManager
    WEBSOCKET_AVAILABLE = True
except ImportError:
    ThreadedWebsocketManager = None
    WEBSOCKET_AVAILABLE = False


class DataProvider:
    """Base class for data providers"""
    
    def __init__(self, timezone: str = 'UTC'):
        self.timezone = timezone
        
    def get_historical_data(self, symbol: str, interval: str, days_back: int) -> pd.DataFrame:
        """Get historical OHLCV data"""
        raise NotImplementedError
        
    def start_real_time_stream(self, symbol: str, interval: str, callback: Callable) -> None:
        """Start real-time data stream"""
        raise NotImplementedError
        
    def stop_real_time_stream(self) -> None:
        """Stop real-time data stream"""
        raise NotImplementedError


class BinanceDataProvider(DataProvider):
    """Binance data provider for cryptocurrency data"""
    
    def __init__(self, timezone: str = 'UTC', api_key: str = None, api_secret: str = None):
        super().__init__(timezone)
        self.client = Client(api_key, api_secret)
        self.ws_manager = None
        self.stream_callback = None
        
    def get_historical_data(self, symbol: str, interval: str, days_back: int) -> pd.DataFrame:
        """Fetch historical price data from Binance"""
        try:
            start_time = datetime.now() - timedelta(days=days_back)
            start_str = start_time.strftime('%Y-%m-%d')
            
            klines = self.client.get_historical_klines(symbol, interval, start_str)
            
            if not klines:
                raise ValueError(f"No data found for {symbol}")
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert timestamp and set as index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Convert from UTC to specified timezone
            if self.timezone != 'UTC':
                try:
                    utc = pytz.UTC
                    target_tz = pytz.timezone(self.timezone)
                    df['timestamp'] = df['timestamp'].dt.tz_localize(utc).dt.tz_convert(target_tz)
                    print(f"Converted timestamps from UTC to {self.timezone}")
                except Exception as e:
                    print(f"Warning: Could not convert to timezone {self.timezone}, using UTC. Error: {e}")
            
            df.set_index('timestamp', inplace=True)
            
            # Convert price columns to numeric
            price_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in price_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Standardize column names
            df.rename(columns={
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }, inplace=True)
            
            result_df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            print(f"Fetched {len(result_df)} {interval} candles for {symbol}")
            return result_df
            
        except Exception as e:
            raise ValueError(f"Error fetching data for {symbol}: {str(e)}")
    
    def start_real_time_stream(self, symbol: str, interval: str, callback: Callable) -> None:
        """Start real-time kline stream from Binance"""
        if not WEBSOCKET_AVAILABLE:
            print("Warning: WebSocket not available. Real-time streaming disabled.")
            return
            
        if self.ws_manager:
            self.stop_real_time_stream()
            
        self.stream_callback = callback
        self.ws_manager = ThreadedWebsocketManager()
        self.ws_manager.start()
        
        def handle_socket_message(msg):
            """Process incoming websocket message"""
            try:
                kline_data = msg['k']
                
                # Convert to standardized format
                candle = {
                    'timestamp': pd.to_datetime(kline_data['t'], unit='ms'),
                    'Open': float(kline_data['o']),
                    'High': float(kline_data['h']),
                    'Low': float(kline_data['l']),
                    'Close': float(kline_data['c']),
                    'Volume': float(kline_data['v']),
                    'is_closed': kline_data['x']  # True when kline is closed
                }
                
                # Apply timezone conversion
                if self.timezone != 'UTC':
                    try:
                        utc = pytz.UTC
                        target_tz = pytz.timezone(self.timezone)
                        candle['timestamp'] = candle['timestamp'].tz_localize(utc).tz_convert(target_tz)
                    except Exception:
                        pass  # Keep UTC if conversion fails
                
                # Call the registered callback
                if self.stream_callback:
                    self.stream_callback(candle)
                    
            except Exception as e:
                print(f"Error processing websocket message: {e}")
        
        # Start kline stream
        self.ws_manager.start_kline_socket(
            callback=handle_socket_message,
            symbol=symbol.lower(),
            interval=interval
        )
        
        print(f"Started real-time stream for {symbol} {interval}")
    
    def stop_real_time_stream(self) -> None:
        """Stop the real-time websocket stream"""
        if self.ws_manager:
            self.ws_manager.stop()
            self.ws_manager = None
            self.stream_callback = None
            print("Stopped real-time stream")


class DataManager:
    """Manages data providers and provides unified interface"""
    
    def __init__(self, provider: DataProvider):
        self.provider = provider
        self.current_data = None
        self.real_time_callbacks = []
        
    def get_historical_data(self, symbol: str, interval: str, days_back: int) -> pd.DataFrame:
        """Get historical data through the provider"""
        self.current_data = self.provider.get_historical_data(symbol, interval, days_back)
        return self.current_data
    
    def add_real_time_callback(self, callback: Callable) -> None:
        """Add callback for real-time data updates"""
        self.real_time_callbacks.append(callback)
    
    def start_real_time_feed(self, symbol: str, interval: str) -> None:
        """Start real-time data feed"""
        def data_callback(candle_data):
            # Notify all registered callbacks
            for callback in self.real_time_callbacks:
                try:
                    callback(candle_data)
                except Exception as e:
                    print(f"Error in callback: {e}")
        
        self.provider.start_real_time_stream(symbol, interval, data_callback)
    
    def stop_real_time_feed(self) -> None:
        """Stop real-time data feed"""
        self.provider.stop_real_time_stream()
    
    def export_data_json(self, data: pd.DataFrame = None) -> str:
        """Export data as JSON for frontend consumption"""
        if data is None:
            data = self.current_data
            
        if data is None:
            return "{}"
            
        # Convert DataFrame to JSON format suitable for charting libraries
        result = {
            "timestamps": data.index.astype(str).tolist(),
            "ohlcv": data[['Open', 'High', 'Low', 'Close', 'Volume']].to_dict('records'),
            "metadata": {
                "symbol": getattr(self, 'current_symbol', 'UNKNOWN'),
                "interval": getattr(self, 'current_interval', 'UNKNOWN'),
                "timezone": self.provider.timezone,
                "last_updated": datetime.now().isoformat()
            }
        }
        
        return json.dumps(result, default=str)
