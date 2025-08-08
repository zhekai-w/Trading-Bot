# 📈 Interactive MACD Trading Strategy

A professional cryptocurrency trading strategy using MACD indicators with interactive TradingView-style charts.

## 🚀 Features

- **MACD Crossover Strategy**: Entry when MACD crosses above Signal line while both are below zero
- **Risk Management**: 2% take profit, 1% stop loss
- **Interactive Charts**: TradingView-style plots with Plotly
- **Timezone Support**: Display timestamps in your local timezone
- **Cryptocurrency Trading**: Uses Binance API for real-time data
- **Multiple Timeframes**: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M

## 🛠️ Setup Instructions

### 1. Create Conda Environment

```bash
# Create environment with Python 3.10
conda create -n trading_env python=3.10 -y

# Activate environment
conda activate trading_env
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

### 3. Run the Strategy

#### Option A: Using the convenience script
```bash
./run_trading.sh
```

#### Option B: Manual execution
```bash
# Activate environment
conda activate trading_env

# Run strategy
python interactive_macd_strategy.py
```

## 📊 Viewing Charts

After running the strategy, an interactive HTML chart will be generated:

### Method 1: Direct browser opening
```bash
firefox ROSEUSDT_5m_interactive_macd.html
```

### Method 2: Local HTTP server (recommended)
```bash
# Start local server
python -m http.server 8000

# Open in browser
http://localhost:8000/ROSEUSDT_5m_interactive_macd.html
```

## ⚙️ Configuration

### Customize Trading Parameters

Edit `interactive_macd_strategy.py` to modify:

- **Symbol**: Change `symbol = "ROSEUSDT"` to any Binance trading pair
- **Timeframe**: Change `interval = "5m"` to desired timeframe
- **MACD Settings**: Modify `fast_length`, `slow_length`, `signal_smoothing`
- **Risk Management**: Adjust `take_profit` and `stop_loss` percentages
- **Timezone**: Set your local timezone (e.g., 'US/Eastern', 'Europe/London')

### Example Modifications

```python
# Different trading pair
symbol = "BTCUSDT"

# 15-minute timeframe
interval = "15m" 

# More conservative risk management
take_profit = 0.015  # 1.5%
stop_loss = 0.005    # 0.5%

# Your timezone
timezone = 'US/Eastern'
```

## 📋 Dependencies

- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **python-binance**: Binance API client
- **plotly**: Interactive charting
- **pytz**: Timezone handling

## 🎯 Strategy Logic

1. **Entry Signal**: MACD crosses above Signal line while both indicators are below zero
2. **Take Profit**: Exit when price moves 2% above entry price
3. **Stop Loss**: Exit when price moves 1% below entry price
4. **End of Period**: Close any open position at the end of data

## 📈 Chart Features

- **Candlestick Chart**: Traditional OHLC visualization
- **MACD Indicator**: Main line, signal line, and histogram
- **Trade Markers**: Buy/sell signals with performance data
- **Interactive Controls**: Zoom, pan, hover tooltips
- **Time Range Selector**: Quick access to different time periods
- **TradingView Theme**: Professional dark theme styling

## ⚠️ Disclaimer

This is for educational purposes only. Cryptocurrency trading involves substantial risk of loss. Always:
- Test strategies thoroughly before live trading
- Only invest what you can afford to lose
- Consider transaction costs and slippage
- Use proper risk management

## 🔧 Troubleshooting

### Environment Issues
```bash
# If conda environment isn't working
conda deactivate
conda activate trading_env

# Check Python version
python --version  # Should show 3.10.x
```

### Missing Dependencies
```bash
# Reinstall packages
pip install --upgrade -r requirements.txt
```

### Chart Display Issues
- Use local HTTP server instead of opening HTML directly
- Ensure browser supports modern JavaScript
- Check if any ad blockers are interfering

## 📞 Support

If you encounter issues:
1. Check that all dependencies are installed
2. Verify internet connection for data fetching
3. Ensure trading pair symbol is valid on Binance
4. Check timezone string format
