import pandas as pd
import numpy as np
from binance.client import Client
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

class CryptoMACDTradingStrategy:
    """
    MACD Crossover Trading Strategy for Cryptocurrency
    - Entry: MACD crosses above Signal line while below zero
    - Exit: 2% take profit or 1% stop loss
    - Supports any timeframe including 5-minute intervals
    """
    
    def __init__(self, symbol, days_back=30, interval='5m', fast_length=12, slow_length=26, signal_smoothing=9, source='close', oscillator_ma_type='EMA', signal_line_ma_type='EMA'):
        """
        Initialize the strategy with parameters matching TradingView MACD settings
        
        Parameters:
        - symbol: Crypto pair symbol (e.g., 'ROSEUSDT')
        - days_back: Number of days of historical data to fetch
        - interval: Timeframe ('1m', '5m', '15m', '1h', '1d', etc.)
        - fast_length: Fast EMA period (default 12) - matches "Fast Length"
        - slow_length: Slow EMA period (default 26) - matches "Slow Length"  
        - signal_smoothing: Signal line EMA period (default 9) - matches "Signal Smoothing"
        - source: Price source (default 'close') - matches "Source"
        - oscillator_ma_type: MA type for MACD calculation (default 'EMA') - matches "Oscillator MA Type"
        - signal_line_ma_type: MA type for Signal line (default 'EMA') - matches "Signal Line MA Type"
        """
        self.symbol = symbol
        self.days_back = days_back
        self.interval = interval
        self.fast_length = fast_length
        self.slow_length = slow_length
        self.signal_smoothing = signal_smoothing
        self.source = source.lower()
        self.oscillator_ma_type = oscillator_ma_type.upper()
        self.signal_line_ma_type = signal_line_ma_type.upper()
        
        # For backward compatibility
        self.fast_period = fast_length
        self.slow_period = slow_length
        self.signal_period = signal_smoothing
        self.take_profit = 0.02  # 2%
        self.stop_loss = 0.01    # 1%
        self.data = None
        self.trades = []
        
        # Initialize Binance client (public API, no authentication needed for historical data)
        self.client = Client()
        
    def fetch_data(self):
        """Fetch historical price data from Binance"""
        try:
            # Calculate start time
            start_time = datetime.now() - timedelta(days=self.days_back)
            start_str = start_time.strftime('%Y-%m-%d')
            
            # Fetch kline data
            klines = self.client.get_historical_klines(
                self.symbol, 
                self.interval, 
                start_str
            )
            
            if not klines:
                raise ValueError(f"No data found for {self.symbol}")
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert timestamp and set as index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Convert price columns to float
            price_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in price_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Rename columns to match original format
            df.rename(columns={
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }, inplace=True)
            
            self.data = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            print(f"Fetched {len(self.data)} {self.interval} candles for {self.symbol}")
            return self.data
            
        except Exception as e:
            raise ValueError(f"Error fetching data for {self.symbol}: {str(e)}")
    
    def calculate_macd(self):
        """Calculate MACD, Signal line, and Histogram using TradingView settings"""
        # Get the source price (Close, High, Low, Open, etc.)
        if self.source == 'close':
            source_price = self.data['Close']
        elif self.source == 'high':
            source_price = self.data['High']
        elif self.source == 'low':
            source_price = self.data['Low']
        elif self.source == 'open':
            source_price = self.data['Open']
        else:
            source_price = self.data['Close']  # Default to Close
        
        # Calculate EMAs for MACD (Oscillator MA Type)
        if self.oscillator_ma_type == 'EMA':
            ema_fast = source_price.ewm(span=self.fast_length, adjust=False).mean()
            ema_slow = source_price.ewm(span=self.slow_length, adjust=False).mean()
        else:
            # For other MA types, we'll use EMA as default (can be extended)
            ema_fast = source_price.ewm(span=self.fast_length, adjust=False).mean()
            ema_slow = source_price.ewm(span=self.slow_length, adjust=False).mean()
        
        # Calculate MACD line (Oscillator)
        self.data['MACD'] = ema_fast - ema_slow
        
        # Calculate Signal line using Signal Line MA Type
        if self.signal_line_ma_type == 'EMA':
            self.data['Signal'] = self.data['MACD'].ewm(span=self.signal_smoothing, adjust=False).mean()
        else:
            # For other MA types, we'll use EMA as default (can be extended)
            self.data['Signal'] = self.data['MACD'].ewm(span=self.signal_smoothing, adjust=False).mean()
        
        # Calculate Histogram
        self.data['Histogram'] = self.data['MACD'] - self.data['Signal']
        
        # Identify crossovers (shifted values for comparison)
        self.data['MACD_prev'] = self.data['MACD'].shift(1)
        self.data['Signal_prev'] = self.data['Signal'].shift(1)
        
        # Bullish crossover: MACD crosses above Signal while below zero
        self.data['Bullish_Cross'] = (
            (self.data['MACD'] > self.data['Signal']) & 
            (self.data['MACD_prev'] <= self.data['Signal_prev']) &
            (self.data['MACD'] < 0) &
            (self.data['Signal'] < 0)
        )
        
    def backtest(self):
        """Run the backtest and track trades"""
        position = None
        entry_price = 0
        entry_date = None
        
        for i in range(len(self.data)):
            current_date = self.data.index[i]
            current_price = float(self.data['Close'].iloc[i])
            
            # Check for entry signal
            if position is None and bool(self.data['Bullish_Cross'].iloc[i]):
                position = 'long'
                entry_price = current_price
                entry_date = current_date
                
            # Check for exit conditions
            elif position == 'long':
                # Calculate return
                returns = (current_price - entry_price) / entry_price
                
                # Check take profit
                if returns >= self.take_profit:
                    self.trades.append({
                        'Entry Date': entry_date,
                        'Entry Price': entry_price,
                        'Exit Date': current_date,
                        'Exit Price': current_price,
                        'Return': returns,
                        'Exit Reason': 'Take Profit'
                    })
                    position = None
                    
                # Check stop loss
                elif returns <= -self.stop_loss:
                    self.trades.append({
                        'Entry Date': entry_date,
                        'Entry Price': entry_price,
                        'Exit Date': current_date,
                        'Exit Price': current_price,
                        'Return': returns,
                        'Exit Reason': 'Stop Loss'
                    })
                    position = None
        
        # Close any open position at the end
        if position == 'long':
            final_price = float(self.data['Close'].iloc[-1])
            self.trades.append({
                'Entry Date': entry_date,
                'Entry Price': entry_price,
                'Exit Date': self.data.index[-1],
                'Exit Price': final_price,
                'Return': (final_price - entry_price) / entry_price,
                'Exit Reason': 'End of Period'
            })
    
    def calculate_performance(self):
        """Calculate strategy performance metrics"""
        if not self.trades:
            return {
                'Total Trades': 0,
                'Winning Trades': 0,
                'Losing Trades': 0,
                'Win Rate': 0,
                'Total Return': 0,
                'Average Return': 0,
                'Best Trade': 0,
                'Worst Trade': 0
            }
        
        trades_df = pd.DataFrame(self.trades)
        
        winning_trades = trades_df[trades_df['Return'] > 0]
        losing_trades = trades_df[trades_df['Return'] <= 0]
        
        performance = {
            'Total Trades': len(trades_df),
            'Winning Trades': len(winning_trades),
            'Losing Trades': len(losing_trades),
            'Win Rate': len(winning_trades) / len(trades_df) * 100 if len(trades_df) > 0 else 0,
            'Total Return': trades_df['Return'].sum() * 100,
            'Average Return': trades_df['Return'].mean() * 100,
            'Best Trade': trades_df['Return'].max() * 100,
            'Worst Trade': trades_df['Return'].min() * 100,
            'Take Profit Hits': len(trades_df[trades_df['Exit Reason'] == 'Take Profit']),
            'Stop Loss Hits': len(trades_df[trades_df['Exit Reason'] == 'Stop Loss'])
        }
        
        return performance
    
    def plot_strategy(self):
        """Visualize the strategy with price and MACD indicators"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
        
        # Plot price and entry signals
        ax1.plot(self.data.index, self.data['Close'], label='Close Price', linewidth=1)
        
        # Mark entry points
        entry_points = self.data[self.data['Bullish_Cross']]
        if not entry_points.empty:
            ax1.scatter(entry_points.index, entry_points['Close'], 
                       color='green', marker='^', s=100, label='Buy Signal', zorder=5)
        
        # Mark trade exits
        for trade in self.trades:
            color = 'lime' if trade['Return'] > 0 else 'red'
            ax1.scatter(trade['Exit Date'], trade['Exit Price'], 
                       color=color, marker='v', s=100, zorder=5)
        
        ax1.set_ylabel('Price (USDT)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_title(f'{self.symbol} - MACD Strategy ({self.interval}) | Fast:{self.fast_length} Slow:{self.slow_length} Signal:{self.signal_smoothing}')
        
        # Plot MACD
        ax2.plot(self.data.index, self.data['MACD'], label='MACD', color='blue', linewidth=1)
        ax2.plot(self.data.index, self.data['Signal'], label='Signal', color='red', linewidth=1)
        ax2.bar(self.data.index, self.data['Histogram'], label='Histogram', 
                color='gray', alpha=0.3, width=0.8)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Mark crossover points
        if not entry_points.empty:
            ax2.scatter(entry_points.index, entry_points['MACD'], 
                       color='green', marker='o', s=50, zorder=5)
        
        ax2.set_ylabel('MACD')
        ax2.set_xlabel('Date/Time')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        filename = f'{self.symbol}_{self.interval}_macd_strategy.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart saved as {filename}")
        plt.close()
    
    def run(self):
        """Execute the complete strategy"""
        print(f"Running MACD Strategy for {self.symbol} on {self.interval} timeframe")
        print(f"MACD Settings: Fast={self.fast_length}, Slow={self.slow_length}, Signal={self.signal_smoothing}")
        print(f"Source: {self.source.capitalize()}, Oscillator MA: {self.oscillator_ma_type}, Signal MA: {self.signal_line_ma_type}")
        print("=" * 80)
        
        # Fetch data
        self.fetch_data()
        
        # Calculate indicators
        self.calculate_macd()
        print("MACD indicators calculated")
        
        # Run backtest
        self.backtest()
        print(f"Backtest complete: {len(self.trades)} trades executed")
        
        # Calculate performance
        performance = self.calculate_performance()
        
        print(f"\nPerformance Summary ({self.days_back} days, {self.interval} timeframe):")
        print("-" * 50)
        for key, value in performance.items():
            if 'Return' in key or 'Rate' in key:
                print(f"{key}: {value:.2f}%")
            else:
                print(f"{key}: {value}")
        
        # Display trade details
        if self.trades:
            print("\nTrade Details:")
            print("-" * 50)
            trades_df = pd.DataFrame(self.trades)
            trades_df['Return'] = trades_df['Return'] * 100  # Convert to percentage
            trades_df['Entry Price'] = trades_df['Entry Price'].round(6)
            trades_df['Exit Price'] = trades_df['Exit Price'].round(6)
            trades_df['Return'] = trades_df['Return'].round(2)
            print(trades_df.to_string())
        
        return performance, self.trades


# Example usage for ROSEUSDT on 5-minute timeframe with TradingView MACD settings
if __name__ == "__main__":
    # Strategy parameters for ROSEUSDT matching TradingView MACD settings
    symbol = "ROSEUSDT"
    days_back = 7  # 7 days of 5-minute data
    interval = "5m"  # 5-minute timeframe
    
    # MACD settings matching the image provided
    fast_length = 12        # Fast Length
    slow_length = 26        # Slow Length  
    signal_smoothing = 9    # Signal Smoothing
    source = 'close'        # Source
    oscillator_ma_type = 'EMA'    # Oscillator MA Type
    signal_line_ma_type = 'EMA'   # Signal Line MA Type
    
    print(f"Testing MACD strategy on {symbol} with {interval} timeframe")
    print(f"Using TradingView MACD settings:")
    print(f"Fast Length: {fast_length}, Slow Length: {slow_length}, Signal Smoothing: {signal_smoothing}")
    print(f"Source: {source}, Oscillator MA: {oscillator_ma_type}, Signal Line MA: {signal_line_ma_type}")
    print("=" * 80)
    
    try:
        # Create and run strategy with TradingView settings
        strategy = CryptoMACDTradingStrategy(
            symbol=symbol, 
            days_back=days_back, 
            interval=interval,
            fast_length=fast_length,
            slow_length=slow_length,
            signal_smoothing=signal_smoothing,
            source=source,
            oscillator_ma_type=oscillator_ma_type,
            signal_line_ma_type=signal_line_ma_type
        )
        performance, trades = strategy.run()
        
        # Plot results
        strategy.plot_strategy()
        
        # Test with different timeframes using same MACD settings
        print(f"\n{'='*80}")
        print("Testing with 15-minute timeframe for comparison (same MACD settings):")
        print("=" * 80)
        
        strategy_15m = CryptoMACDTradingStrategy(
            symbol=symbol, 
            days_back=days_back, 
            interval="15m",
            fast_length=fast_length,
            slow_length=slow_length,
            signal_smoothing=signal_smoothing,
            source=source,
            oscillator_ma_type=oscillator_ma_type,
            signal_line_ma_type=signal_line_ma_type
        )
        performance_15m, trades_15m = strategy_15m.run()
        strategy_15m.plot_strategy()
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have internet connection and the symbol is valid.")
        print("Available intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M")
