import pandas as pd
import numpy as np
from binance.client import Client
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pytz

class InteractiveCryptoMACDStrategy:
    """
    Interactive MACD Crossover Trading Strategy for Cryptocurrency
    - Long entry: MACD crosses above Signal line while both below zero AND price above 200 EMA
    - Short entry: MACD crosses below Signal line while both above zero AND price below 200 EMA
    - Exit: 2% take profit or 1% stop loss (symmetric for long/short)
    - Interactive TradingView-style plots with 200 EMA trend filter
    """
    
    def __init__(self, symbol, days_back=30, interval='5m', fast_length=12, slow_length=26, signal_smoothing=9, source='close', oscillator_ma_type='EMA', signal_line_ma_type='EMA', timezone='UTC'):
        """
        Initialize the strategy with TradingView MACD settings
        
        Parameters:
        - timezone: Target timezone for displaying timestamps (e.g., 'UTC', 'US/Eastern', 'Europe/London', 'Asia/Shanghai', 'Asia/Tokyo')
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
        self.timezone = timezone
        
        # For backward compatibility
        self.fast_period = fast_length
        self.slow_period = slow_length
        self.signal_period = signal_smoothing
        
        self.take_profit = 0.02  # 2%
        self.stop_loss = 0.01    # 1%
        self.data = None
        self.trades = []
        
        # Initialize Binance client
        self.client = Client()
        
    def fetch_data(self):
        """Fetch historical price data from Binance"""
        try:
            start_time = datetime.now() - timedelta(days=self.days_back)
            start_str = start_time.strftime('%Y-%m-%d')
            
            klines = self.client.get_historical_klines(
                self.symbol, 
                self.interval, 
                start_str
            )
            
            if not klines:
                raise ValueError(f"No data found for {self.symbol}")
            
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
            
            price_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in price_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
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
        """Calculate MACD and 200 EMA using TradingView settings"""
        if self.source == 'close':
            source_price = self.data['Close']
        elif self.source == 'high':
            source_price = self.data['High']
        elif self.source == 'low':
            source_price = self.data['Low']
        elif self.source == 'open':
            source_price = self.data['Open']
        else:
            source_price = self.data['Close']
        
        # Calculate MACD
        if self.oscillator_ma_type == 'EMA':
            ema_fast = source_price.ewm(span=self.fast_length, adjust=False).mean()
            ema_slow = source_price.ewm(span=self.slow_length, adjust=False).mean()
        else:
            ema_fast = source_price.ewm(span=self.fast_length, adjust=False).mean()
            ema_slow = source_price.ewm(span=self.slow_length, adjust=False).mean()
        
        self.data['MACD'] = ema_fast - ema_slow
        
        if self.signal_line_ma_type == 'EMA':
            self.data['Signal'] = self.data['MACD'].ewm(span=self.signal_smoothing, adjust=False).mean()
        else:
            self.data['Signal'] = self.data['MACD'].ewm(span=self.signal_smoothing, adjust=False).mean()
        
        self.data['Histogram'] = self.data['MACD'] - self.data['Signal']
        
        # Calculate 200 EMA for trend filter
        self.data['EMA_200'] = self.data['Close'].ewm(span=200, adjust=False).mean()
        
        self.data['MACD_prev'] = self.data['MACD'].shift(1)
        self.data['Signal_prev'] = self.data['Signal'].shift(1)
        
        # Enhanced long signal: MACD cross AND price above 200 EMA
        self.data['Bullish_Cross'] = (
            (self.data['MACD'] > self.data['Signal']) & 
            (self.data['MACD_prev'] <= self.data['Signal_prev']) &
            (self.data['MACD'] < 0) &
            (self.data['Signal'] < 0) &
            (self.data['Close'] > self.data['EMA_200'])  # New: Price above 200 EMA
        )

        # Enhanced short signal: MACD cross down AND price below 200 EMA
        self.data['Bearish_Cross'] = (
            (self.data['MACD'] < self.data['Signal']) &
            (self.data['MACD_prev'] >= self.data['Signal_prev']) &
            (self.data['MACD'] > 0) &
            (self.data['Signal'] > 0) &
            (self.data['Close'] < self.data['EMA_200'])
        )
        
    def backtest(self):
        """Run the backtest and track trades"""
        position = None
        entry_price = 0
        entry_date = None
        
        for i in range(len(self.data)):
            current_date = self.data.index[i]
            current_price = float(self.data['Close'].iloc[i])
            
            if position is None:
                if bool(self.data['Bullish_Cross'].iloc[i]):
                    position = 'long'
                    entry_price = current_price
                    entry_date = current_date
                elif bool(self.data['Bearish_Cross'].iloc[i]):
                    position = 'short'
                    entry_price = current_price
                    entry_date = current_date
                
            elif position == 'long':
                current_high = float(self.data['High'].iloc[i])
                current_low = float(self.data['Low'].iloc[i])
                
                # Calculate target prices
                take_profit_price = entry_price * (1 + self.take_profit)
                stop_loss_price = entry_price * (1 - self.stop_loss)
                
                # Check if high hit take profit first
                if current_high >= take_profit_price:
                    self.trades.append({
                        'Entry Date': entry_date,
                        'Entry Price': entry_price,
                        'Exit Date': current_date,
                        'Exit Price': take_profit_price,  # Use exact TP price
                        'Return': self.take_profit,  # Use exact 2%
                        'Exit Reason': 'Take Profit',
                        'Position': 'Long'
                    })
                    position = None
                    
                # Check if low hit stop loss (only if TP wasn't hit)
                elif current_low <= stop_loss_price:
                    self.trades.append({
                        'Entry Date': entry_date,
                        'Entry Price': entry_price,
                        'Exit Date': current_date,
                        'Exit Price': stop_loss_price,  # Use exact SL price
                        'Return': -self.stop_loss,  # Use exact -1%
                        'Exit Reason': 'Stop Loss',
                        'Position': 'Long'
                    })
                    position = None
            
            elif position == 'short':
                current_high = float(self.data['High'].iloc[i])
                current_low = float(self.data['Low'].iloc[i])
                
                # For shorts, profit target is lower price; stop loss is higher price
                take_profit_price = entry_price * (1 - self.take_profit)
                stop_loss_price = entry_price * (1 + self.stop_loss)
                
                # Check if low hit take profit first (favorable for shorts)
                if current_low <= take_profit_price:
                    self.trades.append({
                        'Entry Date': entry_date,
                        'Entry Price': entry_price,
                        'Exit Date': current_date,
                        'Exit Price': take_profit_price,
                        'Return': self.take_profit,
                        'Exit Reason': 'Take Profit',
                        'Position': 'Short'
                    })
                    position = None
                
                # Check if high hit stop loss (only if TP wasn't hit)
                elif current_high >= stop_loss_price:
                    self.trades.append({
                        'Entry Date': entry_date,
                        'Entry Price': entry_price,
                        'Exit Date': current_date,
                        'Exit Price': stop_loss_price,
                        'Return': -self.stop_loss,
                        'Exit Reason': 'Stop Loss',
                        'Position': 'Short'
                    })
                    position = None
        
        if position is not None:
            final_price = float(self.data['Close'].iloc[-1])
            if position == 'long':
                ret = (final_price - entry_price) / entry_price
                pos_str = 'Long'
            else:  # short
                ret = (entry_price - final_price) / entry_price
                pos_str = 'Short'
            self.trades.append({
                'Entry Date': entry_date,
                'Entry Price': entry_price,
                'Exit Date': self.data.index[-1],
                'Exit Price': final_price,
                'Return': ret,
                'Exit Reason': 'End of Period',
                'Position': pos_str
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
    
    def create_interactive_plot(self):
        """Create clean TradingView-style interactive plot with only essential elements"""
        # Create subplots: 2 rows (Price + MACD)
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(f'{self.symbol} Price Chart', 'MACD Indicator'),
            row_heights=[0.7, 0.3]
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=self.data.index,
                open=self.data['Open'],
                high=self.data['High'],
                low=self.data['Low'],
                close=self.data['Close'],
                name='Price',
                increasing_line_color='#00ff88',  # TradingView green
                decreasing_line_color='#ff4976',  # TradingView red
                increasing_fillcolor='#00ff88',
                decreasing_fillcolor='#ff4976'
            ),
            row=1, col=1
        )
        
        # 200 EMA line
        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.data['EMA_200'],
                mode='lines',
                name='200 EMA',
                line=dict(color='#FFD700', width=2),  # Gold color for 200 EMA
                hovertemplate='<b>200 EMA</b><br>Value: %{y:.6f}<br>Date: %{x}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Entry signals (Buy signals)
        entry_points = self.data[self.data['Bullish_Cross']]
        if not entry_points.empty:
            fig.add_trace(
                go.Scatter(
                    x=entry_points.index,
                    y=entry_points['Close'],
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up',
                        size=15,
                        color='#00ff88',
                        line=dict(width=2, color='white')
                    ),
                    name='Buy Signal',
                    hovertemplate='<b>Buy Signal</b><br>Price: %{y:.6f}<br>Date: %{x}<extra></extra>'
                ),
                row=1, col=1
            )

        # Entry signals (Short signals)
        short_entry_points = self.data[self.data['Bearish_Cross']]
        if not short_entry_points.empty:
            fig.add_trace(
                go.Scatter(
                    x=short_entry_points.index,
                    y=short_entry_points['Close'],
                    mode='markers',
                    marker=dict(
                        symbol='diamond',
                        size=15,
                        color='#42a5f5',
                        line=dict(width=2, color='white')
                    ),
                    name='Short Signal',
                    hovertemplate='<b>Short Signal</b><br>Price: %{y:.6f}<br>Date: %{x}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # Trade exit points - separated by position (Long vs Short) with distinct colors
        if self.trades:
            long_exits = [t for t in self.trades if t.get('Position') == 'Long']
            short_exits = [t for t in self.trades if t.get('Position') == 'Short']

            if long_exits:
                exit_dates = [t['Exit Date'] for t in long_exits]
                exit_prices = [t['Exit Price'] for t in long_exits]
                exit_returns = [t['Return'] for t in long_exits]
                exit_reasons = [t['Exit Reason'] for t in long_exits]
                colors = ['#00ff88' if ret > 0 else '#ff4976' for ret in exit_returns]
                fig.add_trace(
                    go.Scatter(
                        x=exit_dates,
                        y=exit_prices,
                        mode='markers',
                        marker=dict(
                            symbol='triangle-down',
                            size=12,
                            color=colors,
                            line=dict(width=2, color='white')
                        ),
                        name='Close Long',
                        hovertemplate='<b>Close Long</b><br>Price: %{y:.6f}<br>Return: %{customdata:.2f}%<br>Reason: %{text}<br>Date: %{x}<extra></extra>',
                        customdata=[ret*100 for ret in exit_returns],
                        text=exit_reasons
                    ),
                    row=1, col=1
                )

            if short_exits:
                exit_dates = [t['Exit Date'] for t in short_exits]
                exit_prices = [t['Exit Price'] for t in short_exits]
                exit_returns = [t['Return'] for t in short_exits]
                exit_reasons = [t['Exit Reason'] for t in short_exits]
                # Different palette for shorts: profit = blue, loss = orange
                colors = ['#42a5f5' if ret > 0 else '#ff9800' for ret in exit_returns]
                fig.add_trace(
                    go.Scatter(
                        x=exit_dates,
                        y=exit_prices,
                        mode='markers',
                        marker=dict(
                            symbol='x',
                            size=12,
                            color=colors,
                            line=dict(width=2, color='white')
                        ),
                        name='Close Short',
                        hovertemplate='<b>Close Short</b><br>Price: %{y:.6f}<br>Return: %{customdata:.2f}%<br>Reason: %{text}<br>Date: %{x}<extra></extra>',
                        customdata=[ret*100 for ret in exit_returns],
                        text=exit_reasons
                    ),
                    row=1, col=1
                )
        
        # MACD Line
        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.data['MACD'],
                mode='lines',
                name='MACD',
                line=dict(color='#2196F3', width=2),
                hovertemplate='<b>MACD</b><br>Value: %{y:.8f}<br>Date: %{x}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Signal Line
        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.data['Signal'],
                mode='lines',
                name='Signal',
                line=dict(color='#FF5722', width=2),
                hovertemplate='<b>Signal</b><br>Value: %{y:.8f}<br>Date: %{x}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Histogram
        colors = ['#00ff88' if val >= 0 else '#ff4976' for val in self.data['Histogram']]
        fig.add_trace(
            go.Bar(
                x=self.data.index,
                y=self.data['Histogram'],
                name='Histogram',
                marker_color=colors,
                opacity=0.6,
                hovertemplate='<b>Histogram</b><br>Value: %{y:.8f}<br>Date: %{x}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Zero line for MACD
        fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5, row=2, col=1)
        
        # MACD crossover points (bullish)
        if not entry_points.empty:
            fig.add_trace(
                go.Scatter(
                    x=entry_points.index,
                    y=entry_points['MACD'],
                    mode='markers',
                    marker=dict(
                        symbol='circle',
                        size=8,
                        color='#00ff88',
                        line=dict(width=2, color='white')
                    ),
                    name='MACD Cross',
                    hovertemplate='<b>MACD Crossover</b><br>MACD: %{y:.8f}<br>Date: %{x}<extra></extra>',
                    showlegend=False
                ),
                row=2, col=1
            )

        # MACD crossover points (bearish)
        if not short_entry_points.empty:
            fig.add_trace(
                go.Scatter(
                    x=short_entry_points.index,
                    y=short_entry_points['MACD'],
                    mode='markers',
                    marker=dict(
                        symbol='circle',
                        size=8,
                        color='#42a5f5',
                        line=dict(width=2, color='white')
                    ),
                    name='MACD Cross (Bearish)',
                    hovertemplate='<b>MACD Bearish Crossover</b><br>MACD: %{y:.8f}<br>Date: %{x}<extra></extra>',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Update layout with TradingView-style theme
        fig.update_layout(
            title=dict(
                text=f'{self.symbol} - MACD + 200 EMA Strategy ({self.interval}) | Fast:{self.fast_length} Slow:{self.slow_length} Signal:{self.signal_smoothing}',
                x=0.5,
                font=dict(size=16, color='white')
            ),
            plot_bgcolor='#131722',  # TradingView dark background
            paper_bgcolor='#131722',
            font=dict(color='white'),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0)'
            ),
            height=800,
            margin=dict(l=60, r=60, t=80, b=60)
        )
        
        # Update axes
        fig.update_xaxes(
            gridcolor='#363C4E',
            showgrid=True,
            zeroline=False,
            rangeslider_visible=False
        )
        
        fig.update_yaxes(
            gridcolor='#363C4E',
            showgrid=True,
            zeroline=False
        )
        
        # Add range selector
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1H", step="hour", stepmode="backward"),
                        dict(count=4, label="4H", step="hour", stepmode="backward"),
                        dict(count=1, label="1D", step="day", stepmode="backward"),
                        dict(count=3, label="3D", step="day", stepmode="backward"),
                        dict(count=7, label="1W", step="day", stepmode="backward"),
                        dict(step="all")
                    ]),
                    bgcolor='#363C4E',
                    activecolor='#2196F3',
                    font=dict(color='white')
                ),
                type="date"
            )
        )
        
        return fig
    
    def create_interactive_dashboard(self):
        """Create a comprehensive interactive dashboard with parameter controls"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{self.symbol} Interactive MACD Strategy Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            background-color: #131722;
            color: white;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        .dashboard {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .controls {{
            background-color: #1E222D;
            padding: 20px;
            border-radius: 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}
        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        .control-group label {{
            font-size: 12px;
            color: #B8BCC8;
        }}
        .control-group select,
        .control-group input {{
            background-color: #2A2E39;
            color: white;
            border: 1px solid #363C4E;
            border-radius: 4px;
            padding: 8px;
            font-size: 14px;
        }}
        .btn {{
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn:hover {{
            background-color: #1976D2;
        }}
        .stats {{
            background-color: #1E222D;
            padding: 15px;
            border-radius: 8px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 18px;
            font-weight: bold;
            color: #00ff88;
        }}
        .stat-label {{
            font-size: 12px;
            color: #B8BCC8;
        }}
        #chart {{
            height: 800px;
            background-color: #131722;
        }}
        .loading {{
            text-align: center;
            padding: 20px;
            color: #B8BCC8;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>{self.symbol} Interactive MACD Strategy Dashboard</h1>
        
        <div class="controls">
            <div class="control-group">
                <label>Symbol:</label>
                <input type="text" id="symbol" value="{self.symbol}" placeholder="e.g., BTCUSDT">
            </div>
            
            <div class="control-group">
                <label>Timeframe:</label>
                <select id="interval">
                    <option value="1m" {'selected' if self.interval == '1m' else ''}>1 Minute</option>
                    <option value="3m" {'selected' if self.interval == '3m' else ''}>3 Minutes</option>
                    <option value="5m" {'selected' if self.interval == '5m' else ''}>5 Minutes</option>
                    <option value="15m" {'selected' if self.interval == '15m' else ''}>15 Minutes</option>
                    <option value="30m" {'selected' if self.interval == '30m' else ''}>30 Minutes</option>
                    <option value="1h" {'selected' if self.interval == '1h' else ''}>1 Hour</option>
                    <option value="2h" {'selected' if self.interval == '2h' else ''}>2 Hours</option>
                    <option value="4h" {'selected' if self.interval == '4h' else ''}>4 Hours</option>
                    <option value="6h" {'selected' if self.interval == '6h' else ''}>6 Hours</option>
                    <option value="8h" {'selected' if self.interval == '8h' else ''}>8 Hours</option>
                    <option value="12h" {'selected' if self.interval == '12h' else ''}>12 Hours</option>
                    <option value="1d" {'selected' if self.interval == '1d' else ''}>1 Day</option>
                    <option value="3d" {'selected' if self.interval == '3d' else ''}>3 Days</option>
                    <option value="1w" {'selected' if self.interval == '1w' else ''}>1 Week</option>
                </select>
            </div>
            
            <div class="control-group">
                <label>Days Back:</label>
                <input type="number" id="daysBack" value="{self.days_back}" min="1" max="365">
            </div>
            
            <div class="control-group">
                <label>Fast Length:</label>
                <input type="number" id="fastLength" value="{self.fast_length}" min="1" max="50">
            </div>
            
            <div class="control-group">
                <label>Slow Length:</label>
                <input type="number" id="slowLength" value="{self.slow_length}" min="1" max="100">
            </div>
            
            <div class="control-group">
                <label>Signal Smoothing:</label>
                <input type="number" id="signalSmoothing" value="{self.signal_smoothing}" min="1" max="50">
            </div>
            
            <div class="control-group">
                <label>Take Profit %:</label>
                <input type="number" id="takeProfit" value="{self.take_profit * 100}" step="0.1" min="0.1" max="10">
            </div>
            
            <div class="control-group">
                <label>Stop Loss %:</label>
                <input type="number" id="stopLoss" value="{self.stop_loss * 100}" step="0.1" min="0.1" max="10">
            </div>
            
            <button class="btn" onclick="updateStrategy()">Update Strategy</button>
            <button class="btn" onclick="resetToDefaults()">Reset to Defaults</button>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-item">
                <div class="stat-value" id="totalTrades">-</div>
                <div class="stat-label">Total Trades</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="winRate">-</div>
                <div class="stat-label">Win Rate</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="totalReturn">-</div>
                <div class="stat-label">Total Return</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="avgReturn">-</div>
                <div class="stat-label">Avg Return</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="bestTrade">-</div>
                <div class="stat-label">Best Trade</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="worstTrade">-</div>
                <div class="stat-label">Worst Trade</div>
            </div>
        </div>
        
        <div id="chart"></div>
        <div id="loading" class="loading" style="display: none;">
            <p>Loading new strategy data...</p>
        </div>
    </div>

    <script>
        // Initial chart data (from current strategy)
        let currentData = {{
            chartData: {self._get_chart_data_json()},
            performance: {self._get_performance_json()}
        }};
        
        // Display initial chart and stats
        displayChart(currentData.chartData);
        updateStats(currentData.performance);
        
        function displayChart(data) {{
            const layout = {{
                title: {{
                    text: data.title,
                    x: 0.5,
                    font: {{size: 16, color: 'white'}}
                }},
                plot_bgcolor: '#131722',
                paper_bgcolor: '#131722',
                font: {{color: 'white'}},
                showlegend: true,
                legend: {{
                    orientation: "h",
                    yanchor: "bottom",
                    y: 1.02,
                    xanchor: "right",
                    x: 1,
                    bgcolor: 'rgba(0,0,0,0)'
                }},
                height: 800,
                margin: {{l: 60, r: 60, t: 80, b: 60}},
                xaxis: {{
                    gridcolor: '#363C4E',
                    showgrid: true,
                    zeroline: false,
                    rangeslider: {{visible: false}},
                    rangeselector: {{
                        buttons: [
                            {{count: 1, label: "1H", step: "hour", stepmode: "backward"}},
                            {{count: 4, label: "4H", step: "hour", stepmode: "backward"}},
                            {{count: 1, label: "1D", step: "day", stepmode: "backward"}},
                            {{count: 3, label: "3D", step: "day", stepmode: "backward"}},
                            {{count: 7, label: "1W", step: "day", stepmode: "backward"}},
                            {{step: "all"}}
                        ],
                        bgcolor: '#363C4E',
                        activecolor: '#2196F3',
                        font: {{color: 'white'}}
                    }},
                    type: "date"
                }},
                yaxis: {{
                    gridcolor: '#363C4E',
                    showgrid: true,
                    zeroline: false
                }},
                yaxis2: {{
                    gridcolor: '#363C4E',
                    showgrid: true,
                    zeroline: false
                }},
                grid: {{rows: 2, columns: 1, pattern: 'independent', roworder: 'top to bottom'}}
            }};
            
            Plotly.newPlot('chart', data.traces, layout, {{responsive: true}});
        }}
        
        function updateStats(performance) {{
            document.getElementById('totalTrades').textContent = performance.totalTrades || 0;
            document.getElementById('winRate').textContent = (performance.winRate || 0).toFixed(1) + '%';
            document.getElementById('totalReturn').textContent = (performance.totalReturn || 0).toFixed(2) + '%';
            document.getElementById('avgReturn').textContent = (performance.avgReturn || 0).toFixed(2) + '%';
            document.getElementById('bestTrade').textContent = (performance.bestTrade || 0).toFixed(2) + '%';
            document.getElementById('worstTrade').textContent = (performance.worstTrade || 0).toFixed(2) + '%';
        }}
        
        function updateStrategy() {{
            const loading = document.getElementById('loading');
            loading.style.display = 'block';
            
            // Get current parameter values
            const params = {{
                symbol: document.getElementById('symbol').value,
                interval: document.getElementById('interval').value,
                daysBack: parseInt(document.getElementById('daysBack').value),
                fastLength: parseInt(document.getElementById('fastLength').value),
                slowLength: parseInt(document.getElementById('slowLength').value),
                signalSmoothing: parseInt(document.getElementById('signalSmoothing').value),
                takeProfit: parseFloat(document.getElementById('takeProfit').value) / 100,
                stopLoss: parseFloat(document.getElementById('stopLoss').value) / 100
            }};
            
            // Note: In a real implementation, this would make an API call to your backend
            // For now, we'll show a message about the limitation
            setTimeout(() => {{
                loading.style.display = 'none';
                alert('To enable real-time parameter updates, you would need to:\\n\\n' +
                      '1. Set up a web server (Flask/FastAPI)\\n' +
                      '2. Create API endpoints for strategy calculation\\n' +
                      '3. Connect this frontend to the backend\\n\\n' +
                      'Current parameters would be:\\n' + JSON.stringify(params, null, 2));
            }}, 1000);
        }}
        
        function resetToDefaults() {{
            document.getElementById('symbol').value = '{self.symbol}';
            document.getElementById('interval').value = '{self.interval}';
            document.getElementById('daysBack').value = '30';
            document.getElementById('fastLength').value = '12';
            document.getElementById('slowLength').value = '26';
            document.getElementById('signalSmoothing').value = '9';
            document.getElementById('takeProfit').value = '2';
            document.getElementById('stopLoss').value = '1';
        }}
    </script>
</body>
</html>"""
        return html_content
    
    def _get_chart_data_json(self):
        """Get chart data in JSON format for the dashboard"""
        import json
        
        # Generate the plotly figure
        fig = self.create_interactive_plot()
        
        # Extract data for JSON serialization
        chart_data = {
            "title": f"{self.symbol} - MACD + 200 EMA Strategy ({self.interval})",
            "traces": []
        }
        
        for trace in fig.data:
            # Handle candlestick trace separately
            if trace.type == 'candlestick':
                trace_dict = {
                    "x": [
                        (x.isoformat() if hasattr(x, 'isoformat') else str(x))
                        for x in trace.x
                    ],  # ISO timestamps for reliable timezone parsing
                    "open": list(trace.open),
                    "high": list(trace.high),
                    "low": list(trace.low),
                    "close": list(trace.close),
                    "type": trace.type,
                    "name": trace.name,
                    "yaxis": getattr(trace, 'yaxis', 'y'),
                    "xaxis": getattr(trace, 'xaxis', 'x')
                }
            else:
                # Handle other trace types (scatter, bar, etc.)
                trace_dict = {
                    "x": [
                        (x.isoformat() if hasattr(x, 'isoformat') else str(x))
                        for x in trace.x
                    ] if hasattr(trace, 'x') else [],
                    "y": list(trace.y) if hasattr(trace, 'y') else [],
                    "type": trace.type,
                    "name": trace.name,
                    "yaxis": getattr(trace, 'yaxis', 'y'),
                    "xaxis": getattr(trace, 'xaxis', 'x')
                }
                
                # Add optional attributes if they exist
                if hasattr(trace, 'mode'):
                    trace_dict["mode"] = trace.mode
                    
                # Handle line attributes safely
                if hasattr(trace, 'line') and trace.line:
                    try:
                        line_dict = {}
                        if hasattr(trace.line, 'color'):
                            line_dict['color'] = trace.line.color
                        if hasattr(trace.line, 'width'):
                            line_dict['width'] = trace.line.width
                        if line_dict:
                            trace_dict["line"] = line_dict
                    except:
                        pass
                        
                # Handle marker attributes safely  
                if hasattr(trace, 'marker') and trace.marker:
                    try:
                        marker_dict = {}
                        if hasattr(trace.marker, 'color'):
                            marker_dict['color'] = trace.marker.color
                        if hasattr(trace.marker, 'size'):
                            marker_dict['size'] = trace.marker.size
                        if hasattr(trace.marker, 'symbol'):
                            marker_dict['symbol'] = trace.marker.symbol
                        if marker_dict:
                            trace_dict["marker"] = marker_dict
                    except:
                        pass
                        
                # Handle bar chart marker_color
                if hasattr(trace, 'marker_color'):
                    try:
                        if hasattr(trace.marker_color, '__iter__') and not isinstance(trace.marker_color, str):
                            trace_dict["marker_color"] = list(trace.marker_color)
                        else:
                            trace_dict["marker_color"] = trace.marker_color
                    except:
                        pass
            
            chart_data["traces"].append(trace_dict)
        
        return json.dumps(chart_data, default=str)
    
    def _get_performance_json(self):
        """Get performance data in JSON format"""
        import json
        performance = self.calculate_performance()
        return json.dumps({
            "totalTrades": performance.get('Total Trades', 0),
            "winRate": performance.get('Win Rate', 0),
            "totalReturn": performance.get('Total Return', 0),
            "avgReturn": performance.get('Average Return', 0),
            "bestTrade": performance.get('Best Trade', 0),
            "worstTrade": performance.get('Worst Trade', 0)
        })

    def plot_strategy(self, save_html=True, show_plot=True, interactive_dashboard=False):
        """Create and display/save interactive plot"""
        if interactive_dashboard:
            return self.create_interactive_dashboard_file()
        
        fig = self.create_interactive_plot()
        
        if save_html:
            filename = f'{self.symbol}_{self.interval}_interactive_macd.html'
            fig.write_html(filename)
            print(f"Interactive chart saved as {filename}")
        
        if show_plot:
            fig.show()
        
        return fig
    
    def create_interactive_dashboard_file(self):
        """Create and save the interactive dashboard HTML file"""
        html_content = self.create_interactive_dashboard()
        filename = f'{self.symbol}_{self.interval}_interactive_dashboard.html'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Interactive dashboard saved as {filename}")
        print(f"Features included:")
        print(f"  ✓ Dynamic timeframe selection")
        print(f"  ✓ Real-time MACD parameter adjustment")
        print(f"  ✓ Take profit / Stop loss controls")
        print(f"  ✓ Performance metrics display")
        print(f"  ✓ TradingView-style interface")
        print(f"")
        print(f"Note: For real-time updates, consider setting up a web server with Flask/FastAPI")
        
        return filename
    
    def run(self):
        """Execute the complete strategy"""
        print(f"Running Interactive MACD + 200 EMA Strategy for {self.symbol} on {self.interval} timeframe")
        print(f"MACD Settings: Fast={self.fast_length}, Slow={self.slow_length}, Signal={self.signal_smoothing}")
        print(f"Source: {self.source.capitalize()}, Oscillator MA: {self.oscillator_ma_type}, Signal MA: {self.signal_line_ma_type}")
        print(f"Trend Filter: 200 EMA (Price must be above 200 EMA)")
        print(f"Timezone: {self.timezone}")
        print("=" * 80)
        
        # Fetch data
        self.fetch_data()
        
        # Calculate indicators
        self.calculate_macd()
        print("MACD indicators and 200 EMA calculated")
        
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
            trades_df['Return'] = trades_df['Return'] * 100
            trades_df['Entry Price'] = trades_df['Entry Price'].round(6)
            trades_df['Exit Price'] = trades_df['Exit Price'].round(6)
            trades_df['Return'] = trades_df['Return'].round(2)
            print(trades_df.to_string())
        
        return performance, self.trades


# Example usage for interactive ROSEUSDT analysis
if __name__ == "__main__":
    # Configuration for multiple timeframes
    symbol = "ROSEUSDT"
    days_back = 30  # Backtest period
    # intervals = ["5m", "15m"]
    intervals = ["5m"]
    
    # Common MACD settings
    fast_length = 12
    slow_length = 26
    signal_smoothing = 9
    source = 'close'
    oscillator_ma_type = 'EMA'
    signal_line_ma_type = 'EMA'
    timezone = 'Asia/Singapore'  # Change to your timezone

    for interval in intervals:
        print(f"\n===== Backtest for {symbol} on {interval} for {days_back} days =====")
        strategy = InteractiveCryptoMACDStrategy(
            symbol=symbol,
            days_back=days_back,
            interval=interval,
            fast_length=fast_length,
            slow_length=slow_length,
            signal_smoothing=signal_smoothing,
            source=source,
            oscillator_ma_type=oscillator_ma_type,
            signal_line_ma_type=signal_line_ma_type,
            timezone=timezone
        )
        performance, trades = strategy.run()

        # Save and generate interactive chart
        filename = f"{symbol}_{interval}_interactive_macd.html"
        strategy.plot_strategy(save_html=True, show_plot=False)
        print(f"Chart saved to {filename}")
        
        # Generate interactive dashboard with controls
        dashboard_filename = strategy.create_interactive_dashboard_file()
        print(f"Interactive dashboard saved to {dashboard_filename}")
        print(f"Open {dashboard_filename} in your browser to:")
        print(f"  • Change timeframes dynamically")
        print(f"  • Adjust MACD parameters")
        print(f"  • Modify risk management settings")
        print(f"  • View real-time performance metrics")
