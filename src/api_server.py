"""
API Server - RESTful API and WebSocket server for real-time data
Provides endpoints for React/React Native frontend
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any

from data_provider import BinanceDataProvider, DataManager
from indicators import MACDCalculator, IndicatorManager, MovingAverageCalculator
from strategy import MACDStrategy, RiskManager, StrategyEngine


class TradingAPI:
    """RESTful API for trading strategy system"""
    
    def __init__(self, port: int = 5000):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'trading_secret_key'
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.port = port
        
        # Initialize components
        self.data_manager = None
        self.indicator_manager = None
        self.strategy_engine = None
        self.real_time_thread = None
        self.is_streaming = False
        
        self.setup_routes()
        self.setup_websocket_handlers()
    
    def setup_routes(self):
        """Setup REST API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
        
        @self.app.route('/api/symbols', methods=['GET'])
        def get_symbols():
            # Return common trading pairs
            symbols = [
                "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
                "LTCUSDT", "BCHUSDT", "XLMUSDT", "EOSUSDT", "TRXUSDT",
                "ROSEUSDT", "SOLUSDT", "AVAXUSDT", "MATICUSDT", "UNIUSDT"
            ]
            return jsonify({"symbols": symbols})
        
        @self.app.route('/api/intervals', methods=['GET'])
        def get_intervals():
            intervals = [
                {"value": "1m", "label": "1 Minute"},
                {"value": "3m", "label": "3 Minutes"},
                {"value": "5m", "label": "5 Minutes"},
                {"value": "15m", "label": "15 Minutes"},
                {"value": "30m", "label": "30 Minutes"},
                {"value": "1h", "label": "1 Hour"},
                {"value": "2h", "label": "2 Hours"},
                {"value": "4h", "label": "4 Hours"},
                {"value": "6h", "label": "6 Hours"},
                {"value": "8h", "label": "8 Hours"},
                {"value": "12h", "label": "12 Hours"},
                {"value": "1d", "label": "1 Day"}
            ]
            return jsonify({"intervals": intervals})
        
        @self.app.route('/api/data/<symbol>/<interval>', methods=['GET'])
        def get_historical_data(symbol, interval):
            try:
                days_back = int(request.args.get('days', 7))
                timezone = request.args.get('timezone', 'UTC')
                
                # Initialize data provider
                provider = BinanceDataProvider(timezone=timezone)
                self.data_manager = DataManager(provider)
                
                # Fetch data
                data = self.data_manager.get_historical_data(symbol, interval, days_back)
                
                # Calculate indicators
                self.indicator_manager = IndicatorManager()
                macd_calc = MACDCalculator()
                ema_200_calc = MovingAverageCalculator(period=200, ma_type='EMA')
                self.indicator_manager.add_indicator('MACD', macd_calc)
                self.indicator_manager.add_indicator('EMA_200', ema_200_calc)
                indicators = self.indicator_manager.calculate_all(data)
                
                # Export data
                data_json = self.data_manager.export_data_json(data)
                indicators_json = self.indicator_manager.export_indicators_json()
                
                return jsonify({
                    "success": True,
                    "data": json.loads(data_json),
                    "indicators": json.loads(indicators_json)
                })
                
            except Exception as e:
                print(f"Error in get_historical_data: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({"success": False, "error": str(e)}), 400
        
        @self.app.route('/api/backtest/<symbol>/<interval>', methods=['POST'])
        def run_backtest(symbol, interval):
            try:
                config = request.get_json()
                days_back = config.get('days_back', 7)
                timezone = config.get('timezone', 'UTC')
                
                # Strategy parameters
                take_profit = config.get('take_profit', 0.02)
                stop_loss = config.get('stop_loss', 0.01)
                
                # MACD parameters
                fast_length = config.get('fast_length', 12)
                slow_length = config.get('slow_length', 26)
                signal_smoothing = config.get('signal_smoothing', 9)
                
                # Initialize components
                provider = BinanceDataProvider(timezone=timezone)
                self.data_manager = DataManager(provider)
                
                # Fetch data
                data = self.data_manager.get_historical_data(symbol, interval, days_back)
                
                # Calculate indicators
                self.indicator_manager = IndicatorManager()
                macd_calc = MACDCalculator(
                    fast_length=fast_length,
                    slow_length=slow_length,
                    signal_smoothing=signal_smoothing
                )
                ema_200_calc = MovingAverageCalculator(period=200, ma_type='EMA')
                self.indicator_manager.add_indicator('MACD', macd_calc)
                self.indicator_manager.add_indicator('EMA_200', ema_200_calc)
                indicators = self.indicator_manager.calculate_all(data)
                
                # Run strategy
                risk_manager = RiskManager(take_profit=take_profit, stop_loss=stop_loss)
                strategy = MACDStrategy(symbol, risk_manager)
                self.strategy_engine = StrategyEngine(strategy)
                
                results = self.strategy_engine.run_backtest(data, indicators)
                
                return jsonify({
                    "success": True,
                    "results": results
                })
                
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400
        
        @self.app.route('/api/stream/start', methods=['POST'])
        def start_real_time_stream():
            try:
                config = request.get_json()
                symbol = config.get('symbol', 'BTCUSDT')
                interval = config.get('interval', '5m')
                timezone = config.get('timezone', 'UTC')
                
                if self.is_streaming:
                    return jsonify({"success": False, "error": "Stream already running"})
                
                # Initialize for real-time
                provider = BinanceDataProvider(timezone=timezone)
                self.data_manager = DataManager(provider)
                
                # Setup real-time callback
                def on_real_time_data(candle_data):
                    self.socketio.emit('market_data', {
                        'symbol': symbol,
                        'interval': interval,
                        'data': candle_data,
                        'timestamp': datetime.now().isoformat()
                    })
                
                self.data_manager.add_real_time_callback(on_real_time_data)
                self.data_manager.start_real_time_feed(symbol, interval)
                self.is_streaming = True
                
                return jsonify({"success": True, "message": f"Started streaming {symbol} {interval}"})
                
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400
        
        @self.app.route('/api/stream/stop', methods=['POST'])
        def stop_real_time_stream():
            try:
                if self.data_manager:
                    self.data_manager.stop_real_time_feed()
                self.is_streaming = False
                
                return jsonify({"success": True, "message": "Stopped real-time stream"})
                
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400
    
    def setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            emit('connection_status', {'status': 'connected'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('subscribe_market_data')
        def handle_subscribe(data):
            symbol = data.get('symbol', 'BTCUSDT')
            interval = data.get('interval', '5m')
            print(f"Client {request.sid} subscribed to {symbol} {interval}")
            
            # Join room for this symbol/interval combination
            room = f"{symbol}_{interval}"
            # join_room(room)  # Uncomment if using rooms
            
            emit('subscription_status', {
                'symbol': symbol,
                'interval': interval,
                'status': 'subscribed'
            })
    
    def run(self, debug: bool = False):
        """Start the API server"""
        print(f"Starting Trading API server on port {self.port}")
        print(f"Endpoints available:")
        print(f"  - GET  /api/health")
        print(f"  - GET  /api/symbols")
        print(f"  - GET  /api/intervals")
        print(f"  - GET  /api/data/<symbol>/<interval>")
        print(f"  - POST /api/backtest/<symbol>/<interval>")
        print(f"  - POST /api/stream/start")
        print(f"  - POST /api/stream/stop")
        print(f"  - WebSocket: /socket.io/")
        
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=debug)


# CLI interface for the API server
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Trading Strategy API Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    api = TradingAPI(port=args.port)
    api.run(debug=args.debug)
