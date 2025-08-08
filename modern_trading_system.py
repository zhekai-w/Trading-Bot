"""
Modern Trading Strategy System - Refactored Architecture
Main entry point that demonstrates the new modular structure
"""

import sys
import os

# Add the current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, current_dir)
sys.path.insert(0, src_dir)

try:
    from data_provider import BinanceDataProvider, DataManager
    from indicators import MACDCalculator, IndicatorManager, MovingAverageCalculator
    from strategy import MACDStrategy, RiskManager, StrategyEngine
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed and you're in the correct directory")
    sys.exit(1)


class ModernTradingSystem:
    """Main trading system that coordinates all components"""
    
    def __init__(self, symbol: str, interval: str = '5m', days_back: int = 7, 
                 timezone: str = 'Asia/Singapore'):
        self.symbol = symbol
        self.interval = interval
        self.days_back = days_back
        self.timezone = timezone
        
        # Initialize components
        self.data_provider = BinanceDataProvider(timezone=timezone)
        self.data_manager = DataManager(self.data_provider)
        self.indicator_manager = IndicatorManager()
        self.strategy_engine = None
        
        # Setup indicators
        self.setup_indicators()
    
    def setup_indicators(self):
        """Setup technical indicators"""
        # MACD with TradingView default settings
        macd_calc = MACDCalculator(
            fast_length=12,
            slow_length=26,
            signal_smoothing=9,
            source='close',
            oscillator_ma_type='EMA',
            signal_line_ma_type='EMA'
        )
        self.indicator_manager.add_indicator('MACD', macd_calc)
        
        # 200 EMA for trend filter
        ema_200_calc = MovingAverageCalculator(
            period=200,
            ma_type='EMA',
            source='close'
        )
        self.indicator_manager.add_indicator('EMA_200', ema_200_calc)
    
    def run_backtest(self, take_profit: float = 0.02, stop_loss: float = 0.01) -> dict:
        """Run backtest with the current configuration"""
        print(f"🚀 Modern Trading System - {self.symbol}")
        print(f"📊 Timeframe: {self.interval} | Period: {self.days_back} days")
        print(f"🌍 Timezone: {self.timezone}")
        print(f"📈 Strategy: MACD Crossover + 200 EMA Trend Filter")
        print("=" * 60)
        
        # 1. Fetch historical data
        print("📈 Fetching historical data...")
        data = self.data_manager.get_historical_data(self.symbol, self.interval, self.days_back)
        
        # 2. Calculate indicators
        print("⚙️  Calculating technical indicators...")
        indicators = self.indicator_manager.calculate_all(data)
        
        # 3. Setup strategy
        print("🎯 Initializing MACD strategy...")
        risk_manager = RiskManager(take_profit=take_profit, stop_loss=stop_loss)
        strategy = MACDStrategy(self.symbol, risk_manager)
        self.strategy_engine = StrategyEngine(strategy)
        
        # 4. Run backtest
        print("⏰ Running backtest...")
        results = self.strategy_engine.run_backtest(data, indicators)
        
        # 5. Display results
        self.display_results(results)
        
        return {
            'data': data,
            'indicators': indicators,
            'results': results
        }
    
    def display_results(self, results: dict):
        """Display backtest results in a formatted way"""
        performance = results['performance']
        trades = results['trades']
        
        print(f"\n📊 Performance Summary:")
        print("-" * 40)
        print(f"Total Trades: {performance['total_trades']}")
        print(f"Winning Trades: {performance['winning_trades']}")
        print(f"Losing Trades: {performance['losing_trades']}")
        print(f"Win Rate: {performance['win_rate']:.2f}%")
        print(f"Total Return: {performance['total_return']:.2f}%")
        print(f"Average Return: {performance['average_return']:.2f}%")
        print(f"Best Trade: {performance['best_trade']:.2f}%")
        print(f"Worst Trade: {performance['worst_trade']:.2f}%")
        print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {performance['max_drawdown']:.2f}%")
        print(f"Take Profit Hits: {performance['take_profit_hits']}")
        print(f"Stop Loss Hits: {performance['stop_loss_hits']}")
        
        if trades:
            print(f"\n📋 Recent Trades (last 5):")
            print("-" * 40)
            for trade in trades[-5:]:
                return_pct = trade['return_pct'] * 100
                entry_date = str(trade['entry_date'])[:19] if hasattr(trade['entry_date'], 'strftime') else str(trade['entry_date'])[:19]
                exit_date = str(trade['exit_date'])[:19] if hasattr(trade['exit_date'], 'strftime') else str(trade['exit_date'])[:19]
                print(f"{entry_date} → {exit_date}")
                print(f"  {trade['entry_price']:.6f} → {trade['exit_price']:.6f}")
                print(f"  Return: {return_pct:+.2f}% ({trade['exit_reason']})")
                print()
    
    def export_for_frontend(self) -> dict:
        """Export data in format suitable for React frontend"""
        if not self.strategy_engine:
            raise ValueError("Run backtest first")
        
        # Get latest data and indicators
        data = self.data_manager.current_data
        indicators = self.indicator_manager.results
        
        # Export everything as JSON-ready format
        return {
            'market_data': {
                'symbol': self.symbol,
                'interval': self.interval,
                'timezone': self.timezone,
                'ohlcv': data.to_dict('records'),
                'timestamps': data.index.astype(str).tolist()
            },
            'indicators': {
                'macd': {
                    'values': indicators['MACD']['MACD'].fillna(None).tolist(),
                    'signal': indicators['MACD']['Signal'].fillna(None).tolist(),
                    'histogram': indicators['MACD']['Histogram'].fillna(None).tolist(),
                    'timestamps': indicators['MACD']['MACD'].index.astype(str).tolist()
                },
                'ema_200': {
                    'values': indicators['EMA_200']['EMA_200'].fillna(None).tolist() if 'EMA_200' in indicators else [],
                    'timestamps': indicators['EMA_200']['EMA_200'].index.astype(str).tolist() if 'EMA_200' in indicators else []
                }
            },
            'strategy_results': self.strategy_engine.export_results_json(),
            'metadata': {
                'last_updated': self.data_manager.provider.timezone,
                'data_points': len(data),
                'timeframe': self.interval
            }
        }
    
    def start_real_time_mode(self):
        """Start real-time trading mode"""
        print(f"🔴 Starting real-time mode for {self.symbol} {self.interval}")
        
        def on_new_candle(candle_data):
            print(f"📊 New candle: {candle_data['Close']:.6f} at {candle_data['timestamp']}")
            
            # In real implementation, you'd:
            # 1. Update indicators with new data
            # 2. Generate new signals
            # 3. Update positions
            # 4. Send updates to frontend via WebSocket
        
        self.data_manager.add_real_time_callback(on_new_candle)
        self.data_manager.start_real_time_feed(self.symbol, self.interval)
        
        if self.strategy_engine:
            self.strategy_engine.start_real_time_trading()
    
    def stop_real_time_mode(self):
        """Stop real-time trading mode"""
        self.data_manager.stop_real_time_feed()
        if self.strategy_engine:
            self.strategy_engine.stop_real_time_trading()
        print("🔴 Real-time mode stopped")


def main():
    """Example usage of the modern trading system"""
    
    # Configuration
    symbol = "ROSEUSDT"
    interval = "5m"
    days_back = 7
    timezone = "Asia/Singapore"
    
    print("🏗️  Modern Trading System v2.0")
    print("=" * 50)
    
    try:
        # Initialize system
        trading_system = ModernTradingSystem(
            symbol=symbol,
            interval=interval,
            days_back=days_back,
            timezone=timezone
        )
        
        # Run backtest
        results = trading_system.run_backtest(
            take_profit=0.02,  # 2%
            stop_loss=0.01     # 1%
        )
        
        print(f"\n✅ Backtest completed successfully!")
        print(f"📊 Data points: {len(results['data'])}")
        print(f"📈 MACD signals: {sum(results['indicators']['MACD']['MACD'] > results['indicators']['MACD']['Signal'])}")
        
        # Export data for frontend (example)
        frontend_data = trading_system.export_for_frontend()
        print(f"📦 Frontend data exported: {len(frontend_data)} sections")
        
        # Real-time mode example (uncomment to test)
        # print(f"\n🔴 Starting real-time mode for 30 seconds...")
        # trading_system.start_real_time_mode()
        # time.sleep(30)
        # trading_system.stop_real_time_mode()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
