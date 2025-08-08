#!/usr/bin/env python3
"""
Interactive MACD Strategy Dashboard Server
This Flask server provides real-time updates for the MACD strategy dashboard.
Run this server and access http://localhost:5000 for the full interactive experience.
"""

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import json
from interactive_macd_strategy import InteractiveCryptoMACDStrategy

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def create_enhanced_dashboard_template():
    """Create the enhanced dashboard template with real API integration"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Interactive MACD Strategy Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            background-color: #131722;
            color: white;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .dashboard {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .controls {
            background-color: #1E222D;
            padding: 20px;
            border-radius: 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .control-group label {
            font-size: 12px;
            color: #B8BCC8;
        }
        .control-group select,
        .control-group input {
            background-color: #2A2E39;
            color: white;
            border: 1px solid #363C4E;
            border-radius: 4px;
            padding: 8px;
            font-size: 14px;
        }
        .btn {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn:hover {
            background-color: #1976D2;
        }
        .btn:disabled {
            background-color: #555;
            cursor: not-allowed;
        }
        .stats {
            background-color: #1E222D;
            padding: 15px;
            border-radius: 8px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-value {
            font-size: 18px;
            font-weight: bold;
            color: #00ff88;
        }
        .stat-label {
            font-size: 12px;
            color: #B8BCC8;
        }
        #chart {
            height: 800px;
            background-color: #131722;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #B8BCC8;
        }
        .error {
            background-color: #ff4976;
            color: white;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .success {
            background-color: #00ff88;
            color: #131722;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>🚀 Interactive MACD Strategy Dashboard</h1>
        
        <div class="controls">
            <div class="control-group">
                <label>Symbol:</label>
                <input type="text" id="symbol" value="ROSEUSDT" placeholder="e.g., BTCUSDT">
            </div>
            
            <div class="control-group">
                <label>Timeframe:</label>
                <select id="interval">
                    <option value="1m">1 Minute</option>
                    <option value="3m">3 Minutes</option>
                    <option value="5m" selected>5 Minutes</option>
                    <option value="15m">15 Minutes</option>
                    <option value="30m">30 Minutes</option>
                    <option value="1h">1 Hour</option>
                    <option value="2h">2 Hours</option>
                    <option value="4h">4 Hours</option>
                    <option value="6h">6 Hours</option>
                    <option value="8h">8 Hours</option>
                    <option value="12h">12 Hours</option>
                    <option value="1d">1 Day</option>
                    <option value="3d">3 Days</option>
                    <option value="1w">1 Week</option>
                </select>
            </div>
            
            <div class="control-group">
                <label>Days Back:</label>
                <input type="number" id="daysBack" value="30" min="1" max="365">
            </div>
            
            <div class="control-group">
                <label>Fast Length:</label>
                <input type="number" id="fastLength" value="12" min="1" max="50">
            </div>
            
            <div class="control-group">
                <label>Slow Length:</label>
                <input type="number" id="slowLength" value="26" min="1" max="100">
            </div>
            
            <div class="control-group">
                <label>Signal Smoothing:</label>
                <input type="number" id="signalSmoothing" value="9" min="1" max="50">
            </div>
            
            <div class="control-group">
                <label>Take Profit %:</label>
                <input type="number" id="takeProfit" value="2" step="0.1" min="0.1" max="10">
            </div>
            
            <div class="control-group">
                <label>Stop Loss %:</label>
                <input type="number" id="stopLoss" value="1" step="0.1" min="0.1" max="10">
            </div>
            
            <button class="btn" id="updateBtn" onclick="updateStrategy()">🔄 Update Strategy</button>
            <button class="btn" onclick="resetToDefaults()">↻ Reset to Defaults</button>
        </div>
        
        <div id="messages"></div>
        
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
            <p>🔄 Loading new strategy data...</p>
        </div>
    </div>

    <script>
        // Load initial data
        window.onload = function() {
            updateStrategy();
        };
        
        function showMessage(message, type = 'success') {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.textContent = message;
            messagesDiv.appendChild(messageDiv);
            
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
        
        function displayChart(data) {
            if (!data || !data.traces) {
                console.error('Invalid chart data received');
                return;
            }
            
            // Convert string dates back to Date objects for Plotly
            data.traces.forEach(trace => {
                if (trace.x && trace.x.length > 0) {
                    trace.x = trace.x.map(dateStr => new Date(dateStr));
                }
            });
            
            const layout = {
                title: {
                    text: data.title,
                    x: 0.5,
                    font: {size: 16, color: 'white'}
                },
                plot_bgcolor: '#131722',
                paper_bgcolor: '#131722',
                font: {color: 'white'},
                showlegend: true,
                legend: {
                    orientation: "h",
                    yanchor: "bottom",
                    y: 1.02,
                    xanchor: "right",
                    x: 1,
                    bgcolor: 'rgba(0,0,0,0)'
                },
                height: 800,
                margin: {l: 60, r: 60, t: 80, b: 60},
                xaxis: {
                    gridcolor: '#363C4E',
                    showgrid: true,
                    zeroline: false,
                    rangeslider: {visible: false},
                    rangeselector: {
                        buttons: [
                            {count: 1, label: "1H", step: "hour", stepmode: "backward"},
                            {count: 4, label: "4H", step: "hour", stepmode: "backward"},
                            {count: 1, label: "1D", step: "day", stepmode: "backward"},
                            {count: 3, label: "3D", step: "day", stepmode: "backward"},
                            {count: 7, label: "1W", step: "day", stepmode: "backward"},
                            {step: "all"}
                        ],
                        bgcolor: '#363C4E',
                        activecolor: '#2196F3',
                        font: {color: 'white'}
                    },
                    type: "date"
                },
                yaxis: {
                    gridcolor: '#363C4E',
                    showgrid: true,
                    zeroline: false
                },
                yaxis2: {
                    gridcolor: '#363C4E',
                    showgrid: true,
                    zeroline: false
                },
                grid: {rows: 2, columns: 1, pattern: 'independent', roworder: 'top to bottom'}
            };
            
            Plotly.newPlot('chart', data.traces, layout, {responsive: true});
        }
        
        function updateStats(performance) {
            document.getElementById('totalTrades').textContent = performance.totalTrades || 0;
            document.getElementById('winRate').textContent = (performance.winRate || 0).toFixed(1) + '%';
            document.getElementById('totalReturn').textContent = (performance.totalReturn || 0).toFixed(2) + '%';
            document.getElementById('avgReturn').textContent = (performance.avgReturn || 0).toFixed(2) + '%';
            document.getElementById('bestTrade').textContent = (performance.bestTrade || 0).toFixed(2) + '%';
            document.getElementById('worstTrade').textContent = (performance.worstTrade || 0).toFixed(2) + '%';
        }
        
        async function updateStrategy() {
            const loading = document.getElementById('loading');
            const updateBtn = document.getElementById('updateBtn');
            
            loading.style.display = 'block';
            updateBtn.disabled = true;
            updateBtn.textContent = '⏳ Processing...';
            
            // Get current parameter values
            const params = {
                symbol: document.getElementById('symbol').value,
                interval: document.getElementById('interval').value,
                days_back: parseInt(document.getElementById('daysBack').value),
                fast_length: parseInt(document.getElementById('fastLength').value),
                slow_length: parseInt(document.getElementById('slowLength').value),
                signal_smoothing: parseInt(document.getElementById('signalSmoothing').value),
                take_profit: parseFloat(document.getElementById('takeProfit').value) / 100,
                stop_loss: parseFloat(document.getElementById('stopLoss').value) / 100
            };
            
            try {
                const response = await fetch('/api/update_strategy', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(params)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                
                if (result.success) {
                    displayChart(result.chart_data);
                    updateStats(result.performance);
                    showMessage(`✅ Strategy updated successfully! Found ${result.performance.totalTrades} trades.`, 'success');
                } else {
                    showMessage(`❌ Error: ${result.error}`, 'error');
                }
                
            } catch (error) {
                console.error('Error updating strategy:', error);
                showMessage(`❌ Network error: ${error.message}`, 'error');
            } finally {
                loading.style.display = 'none';
                updateBtn.disabled = false;
                updateBtn.textContent = '🔄 Update Strategy';
            }
        }
        
        function resetToDefaults() {
            document.getElementById('symbol').value = 'ROSEUSDT';
            document.getElementById('interval').value = '5m';
            document.getElementById('daysBack').value = '30';
            document.getElementById('fastLength').value = '12';
            document.getElementById('slowLength').value = '26';
            document.getElementById('signalSmoothing').value = '9';
            document.getElementById('takeProfit').value = '2';
            document.getElementById('stopLoss').value = '1';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return render_template_string(create_enhanced_dashboard_template())

@app.route('/api/update_strategy', methods=['POST'])
def update_strategy():
    """API endpoint to update strategy with new parameters"""
    try:
        print("=== DEBUG: API endpoint called ===")
        params = request.json
        print(f"DEBUG: Received params: {params}")
        
        # Validate parameters
        required_params = ['symbol', 'interval', 'days_back', 'fast_length', 'slow_length', 'signal_smoothing', 'take_profit', 'stop_loss']
        for param in required_params:
            if param not in params:
                return jsonify({'success': False, 'error': f'Missing parameter: {param}'}), 400
        
        # Create strategy with new parameters
        print("DEBUG: Creating strategy instance...")
        strategy = InteractiveCryptoMACDStrategy(
            symbol=params['symbol'],
            days_back=params['days_back'],
            interval=params['interval'],
            fast_length=params['fast_length'],
            slow_length=params['slow_length'],
            signal_smoothing=params['signal_smoothing']
        )
        print("DEBUG: Strategy instance created successfully")
        
        # Update take profit and stop loss
        strategy.take_profit = params['take_profit']
        strategy.stop_loss = params['stop_loss']
        
        # Run the strategy
        print("DEBUG: Fetching data...")
        strategy.fetch_data()
        print("DEBUG: Calculating MACD...")
        strategy.calculate_macd()
        print("DEBUG: Running backtest...")
        strategy.backtest()
        
        # Get performance metrics
        print("DEBUG: Calculating performance...")
        performance = strategy.calculate_performance()
        
        # Get chart data
        print("DEBUG: Creating chart...")
        fig = strategy.create_interactive_plot()
        print("DEBUG: Chart created successfully")
        
        # Convert chart data to JSON format using the same method as interactive_macd_strategy.py
        print("DEBUG: Converting chart data to JSON...")
        chart_data = {
            "title": f"{params['symbol']} - MACD + 200 EMA Strategy ({params['interval']})",
            "traces": []
        }
        
        print(f"DEBUG: Processing {len(fig.data)} traces...")
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
            print(f"DEBUG: Trace processed successfully: {trace.type} - {trace.name}")
        
        print("DEBUG: Chart data conversion complete")
        
        print("DEBUG: Preparing response...")
        response_data = {
            'success': True,
            'chart_data': chart_data,
            'performance': {
                'totalTrades': performance.get('Total Trades', 0),
                'winRate': performance.get('Win Rate', 0),
                'totalReturn': performance.get('Total Return', 0),
                'avgReturn': performance.get('Average Return', 0),
                'bestTrade': performance.get('Best Trade', 0),
                'worstTrade': performance.get('Worst Trade', 0)
            }
        }
        print("DEBUG: Response prepared successfully")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"ERROR: Exception in update_strategy: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Interactive MACD Strategy Dashboard Server...")
    print("📊 Access the dashboard at: http://localhost:5000")
    print("🔥 Features:")
    print("   • Real-time parameter updates")
    print("   • Dynamic timeframe switching")
    print("   • Interactive TradingView-style charts")
    print("   • Live performance metrics")
    print("   • Risk management controls")
    print("\n🛑 Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
