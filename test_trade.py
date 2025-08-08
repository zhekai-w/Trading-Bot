import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

class MACDTradingStrategy:
    """
    MACD Crossover Trading Strategy
    - Entry: MACD crosses above Signal line while below zero
    - Exit: 2% take profit or 1% stop loss
    """
    
    def __init__(self, symbol, start_date, end_date, fast_period=12, slow_period=26, signal_period=9):
        """
        Initialize the strategy with parameters
        
        Parameters:
        - symbol: Stock ticker symbol
        - start_date: Start date for backtesting
        - end_date: End date for backtesting
        - fast_period: Fast EMA period (default 12)
        - slow_period: Slow EMA period (default 26)
        - signal_period: Signal line EMA period (default 9)
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.take_profit = 0.02  # 2%
        self.stop_loss = 0.01    # 1%
        self.data = None
        self.trades = []
        
    def fetch_data(self):
        """Fetch historical price data"""
        self.data = yf.download(self.symbol, start=self.start_date, end=self.end_date)
        if self.data.empty:
            raise ValueError(f"No data found for {self.symbol}")
        return self.data
    
    def calculate_macd(self):
        """Calculate MACD, Signal line, and Histogram"""
        # Calculate EMAs
        ema_fast = self.data['Close'].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = self.data['Close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # Calculate MACD line
        self.data['MACD'] = ema_fast - ema_slow
        
        # Calculate Signal line
        self.data['Signal'] = self.data['MACD'].ewm(span=self.signal_period, adjust=False).mean()
        
        # Calculate Histogram
        self.data['Histogram'] = self.data['MACD'] - self.data['Signal']
        
        # Identify crossovers
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
            current_price = self.data['Close'].iloc[i]
            
            # Check for entry signal
            if position is None and self.data['Bullish_Cross'].iloc[i]:
                position = 'long'
                entry_price = float(current_price)
                entry_date = current_date
                
            # Check for exit conditions
            elif position == 'long':
                # Calculate return
                current_price_float = float(current_price)
                returns = (current_price_float - entry_price) / entry_price
                
                # Check take profit
                if returns >= self.take_profit:
                    self.trades.append({
                        'Entry Date': entry_date,
                        'Entry Price': entry_price,
                        'Exit Date': current_date,
                        'Exit Price': current_price_float,
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
                        'Exit Price': current_price_float,
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
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Plot price and entry signals
        ax1.plot(self.data.index, self.data['Close'], label='Close Price', linewidth=1)
        
        # Mark entry points
        entry_points = self.data[self.data['Bullish_Cross']]
        ax1.scatter(entry_points.index, entry_points['Close'], 
                   color='green', marker='^', s=100, label='Buy Signal', zorder=5)
        
        # Mark trade exits
        for trade in self.trades:
            color = 'lime' if trade['Return'] > 0 else 'red'
            ax1.scatter(trade['Exit Date'], trade['Exit Price'], 
                       color=color, marker='v', s=100, zorder=5)
        
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_title(f'{self.symbol} - MACD Trading Strategy')
        
        # Plot MACD
        ax2.plot(self.data.index, self.data['MACD'], label='MACD', color='blue')
        ax2.plot(self.data.index, self.data['Signal'], label='Signal', color='red')
        ax2.bar(self.data.index, self.data['Histogram'], label='Histogram', 
                color='gray', alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Mark crossover points
        ax2.scatter(entry_points.index, entry_points['MACD'], 
                   color='green', marker='o', s=50, zorder=5)
        
        ax2.set_ylabel('MACD')
        ax2.set_xlabel('Date')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.symbol}_macd_strategy.png', dpi=300, bbox_inches='tight')
        print(f"Chart saved as {self.symbol}_macd_strategy.png")
        # plt.show()  # Commented out for non-interactive environments
    
    def run(self):
        """Execute the complete strategy"""
        print(f"Running MACD Strategy for {self.symbol}")
        print("=" * 50)
        
        # Fetch data
        self.fetch_data()
        print(f"Data fetched: {len(self.data)} days")
        
        # Calculate indicators
        self.calculate_macd()
        print("MACD indicators calculated")
        
        # Run backtest
        self.backtest()
        print(f"Backtest complete: {len(self.trades)} trades executed")
        
        # Calculate performance
        performance = self.calculate_performance()
        
        print("\nPerformance Summary:")
        print("-" * 30)
        for key, value in performance.items():
            if 'Return' in key or 'Rate' in key:
                print(f"{key}: {value:.2f}%")
            else:
                print(f"{key}: {value}")
        
        # Display trade details
        if self.trades:
            print("\nTrade Details:")
            print("-" * 30)
            trades_df = pd.DataFrame(self.trades)
            trades_df['Return'] = trades_df['Return'] * 100  # Convert to percentage
            print(trades_df.to_string())
        
        return performance, self.trades


# Example usage
if __name__ == "__main__":
    # Strategy parameters
    symbol = "SPY"  # S&P 500 ETF
    start_date = "2023-01-01"
    end_date = "2024-01-01"
    
    # Create and run strategy
    strategy = MACDTradingStrategy(symbol, start_date, end_date)
    performance, trades = strategy.run()
    
    # Plot results
    strategy.plot_strategy()
    
    # Optional: Test with different symbols
    # symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    # for sym in symbols:
    #     print(f"\n{'='*60}")
    #     strategy = MACDTradingStrategy(sym, start_date, end_date)
    #     strategy.run()