#!/usr/bin/env python3
"""
Live Price + Candlestick App for the MACD/200 EMA Strategy

Features:
- Live candlestick chart with TradingView-like styling
- 200 EMA overlay
- Last price marker and ticker
- Controls for symbol, timeframe, and candle limit
- Auto-refresh every 5 seconds (configurable)

Run:
  python live_price_candles_app.py
Then open: http://localhost:5001
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from datetime import datetime
import pytz
import pandas as pd
from binance.client import Client
import numpy as np
import os
import requests


app = Flask(__name__)
CORS(app)


# Telegram configuration via environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Keep track of last-sent signal per (symbol, interval, side)
LAST_SENT_SIGNALS = {}

# Risk settings (defaults align with strategy)
TAKE_PROFIT = float(os.getenv("LIVE_TAKE_PROFIT", "0.02"))
STOP_LOSS = float(os.getenv("LIVE_STOP_LOSS", "0.01"))

# Freshness guard for Telegram alerts (seconds)
TELEGRAM_FRESH_MAX_AGE_SECONDS = int(os.getenv("TELEGRAM_FRESH_MAX_AGE_SECONDS", "30"))


def send_telegram_message(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=5)
    except Exception:
        # Silently ignore to avoid breaking the API
        pass

def format_sgt_time(iso_str: str) -> str:
    try:
        ts = pd.to_datetime(iso_str)
        if ts.tzinfo is None:
            ts = pytz.timezone("Asia/Singapore").localize(ts)
        else:
            ts = ts.tz_convert("Asia/Singapore")
        return ts.strftime("%Y-%m-%d %H:%M SGT")
    except Exception:
        return iso_str


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Live Candles + 200 EMA</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    body { background-color: #131722; color: white; font-family: Arial, sans-serif; margin: 0; padding: 20px; }
    .dashboard { display: flex; flex-direction: column; gap: 16px; }
    .controls { background: #1E222D; padding: 16px; border-radius: 8px; display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
    .control-group { display: flex; gap: 8px; align-items: center; }
    .control-group label { font-size: 12px; color: #B8BCC8; }
    input, select { background: #2A2E39; color: white; border: 1px solid #363C4E; border-radius: 4px; padding: 8px; font-size: 14px; }
    .btn { background: #2196F3; color: white; border: none; padding: 10px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; }
    .btn:hover { background: #1976D2; }
    #chart { height: 800px; background-color: #131722; }
    .row { display: flex; gap: 12px; align-items: center; }
    .ticker { background: #1E222D; padding: 10px 12px; border-radius: 6px; font-weight: bold; }
  </style>
  <script>
    let pollHandle = null;

    async function fetchCandles() {
      const symbol = document.getElementById('symbol').value.trim();
      const interval = document.getElementById('interval').value;
      const limit = parseInt(document.getElementById('limit').value);
      const res = await fetch(`/api/live_klines?symbol=${encodeURIComponent(symbol)}&interval=${encodeURIComponent(interval)}&limit=${limit}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    }

    function displayChart(payload) {
      const times = payload.candles.map(c => new Date(c.t));
      const opens = payload.candles.map(c => c.o);
      const highs = payload.candles.map(c => c.h);
      const lows  = payload.candles.map(c => c.l);
      const closes= payload.candles.map(c => c.c);
      const ema200= payload.ema200 || [];
      const macd  = (payload.macd || []).map(v => v === null ? null : v);
      const signal= (payload.signal || []).map(v => v === null ? null : v);
      const hist  = (payload.histogram || []).map(v => v === null ? null : v);
      const buySigs = payload.buySignals || [];
      const shortSigs = payload.shortSignals || [];
      const closeLong = payload.closeLong || [];
      const closeShort = payload.closeShort || [];

      const candleTrace = {
        type: 'candlestick', name: 'Price', x: times,
        open: opens, high: highs, low: lows, close: closes,
        increasing: { line: { color: '#00ff88' } },
        decreasing: { line: { color: '#ff4976' } },
        yaxis: 'y'
      };

      const emaTrace = {
        type: 'scatter', name: '200 EMA', mode: 'lines', x: times, y: ema200,
        line: { color: '#FFD700', width: 2 },
        hovertemplate: '<b>200 EMA</b><br>%{y:.6f}<extra></extra>',
        yaxis: 'y'
      };

      const lastPrice = payload.lastPrice;
      const lastPointTrace = {
        type: 'scatter', name: 'Last', mode: 'markers', x: [times[times.length - 1]], y: [lastPrice],
        marker: { color: '#ffffff', size: 10, line: { width: 2, color: '#2196F3' } },
        hovertemplate: '<b>Last</b><br>%{y:.6f}<extra></extra>',
        yaxis: 'y'
      };

      // MACD panel traces
      const macdTrace = {
        type: 'scatter', name: 'MACD', mode: 'lines', x: times, y: macd,
        line: { color: '#2196F3', width: 2 }, xaxis: 'x2', yaxis: 'y2',
        hovertemplate: '<b>MACD</b><br>%{y:.8f}<extra></extra>'
      };
      const signalTrace = {
        type: 'scatter', name: 'Signal', mode: 'lines', x: times, y: signal,
        line: { color: '#FF5722', width: 2 }, xaxis: 'x2', yaxis: 'y2',
        hovertemplate: '<b>Signal</b><br>%{y:.8f}<extra></extra>'
      };
      const histColors = hist.map(v => (v ?? 0) >= 0 ? '#00ff88' : '#ff4976');
      const histTrace = {
        type: 'bar', name: 'Histogram', x: times, y: hist, marker: { color: histColors }, opacity: 0.6, xaxis: 'x2', yaxis: 'y2',
        hovertemplate: '<b>Histogram</b><br>%{y:.8f}<extra></extra>'
      };

      const layout = {
        title: { text: `${payload.symbol} (${payload.interval}) - Live Candles + 200 EMA + MACD`, x: 0.5, font: { size: 16, color: 'white' } },
        plot_bgcolor: '#131722', paper_bgcolor: '#131722', font: { color: 'white' },
        showlegend: true,
        legend: { orientation: 'h', y: 1.02, x: 1, xanchor: 'right', bgcolor: 'rgba(0,0,0,0)' },
        height: 800, margin: { l: 60, r: 60, t: 60, b: 60 },
        xaxis: { gridcolor: '#363C4E', showgrid: true, zeroline: false, type: 'date', rangeslider: { visible: false }, rangeselector: { buttons: [
          { count: 1, label: '1H', step: 'hour', stepmode: 'backward' },
          { count: 4, label: '4H', step: 'hour', stepmode: 'backward' },
          { count: 1, label: '1D', step: 'day', stepmode: 'backward' },
          { step: 'all' }
        ], bgcolor: '#363C4E', activecolor: '#2196F3', font: { color: 'white' } } },
        yaxis: { gridcolor: '#363C4E', showgrid: true, zeroline: false },
        xaxis2: { gridcolor: '#363C4E', showgrid: true, zeroline: false, type: 'date', matches: 'x', rangeslider: { visible: false } },
        yaxis2: { gridcolor: '#363C4E', showgrid: true, zeroline: false },
        grid: { rows: 2, columns: 1, pattern: 'coupled', roworder: 'top to bottom' },
        shapes: times && times.length ? [
          { type: 'line', xref: 'x2', yref: 'y2', x0: times[0], x1: times[times.length-1], y0: 0, y1: 0,
            line: { color: 'white', width: 1, dash: 'dot' } }
        ] : []
      };

      // Entry signal markers on price panel
      const buyTrace = {
        type: 'scatter', name: 'Buy Signal', mode: 'markers', yaxis: 'y', x: buySigs.map(s => new Date(s.t)), y: buySigs.map(s => s.p),
        marker: { symbol: 'triangle-up', size: 14, color: '#00ff88', line: { width: 2, color: 'white' } },
        hovertemplate: '<b>Buy</b><br>%{y:.6f}<extra></extra>'
      };
      const shortTrace = {
        type: 'scatter', name: 'Short Signal', mode: 'markers', yaxis: 'y', x: shortSigs.map(s => new Date(s.t)), y: shortSigs.map(s => s.p),
        marker: { symbol: 'diamond', size: 14, color: '#42a5f5', line: { width: 2, color: 'white' } },
        hovertemplate: '<b>Short</b><br>%{y:.6f}<extra></extra>'
      };

      // Close signals (completed exits)
      const longColors = closeLong.map(s => (s.ret ?? 0) > 0 ? '#00ff88' : '#ff4976');
      const closeLongTrace = {
        type: 'scatter', name: 'Close Long', mode: 'markers', yaxis: 'y',
        x: closeLong.map(s => new Date(s.t)), y: closeLong.map(s => s.p),
        marker: { symbol: 'triangle-down', size: 12, color: longColors, line: { width: 2, color: 'white' } },
        customdata: closeLong.map(s => (s.ret ?? 0) * 100),
        text: closeLong.map(s => s.reason || ''),
        hovertemplate: '<b>Close Long</b><br>Price: %{y:.6f}<br>Return: %{customdata:.2f}%<br>Reason: %{text}<extra></extra>'
      };
      const shortColors = closeShort.map(s => (s.ret ?? 0) > 0 ? '#42a5f5' : '#ff9800');
      const closeShortTrace = {
        type: 'scatter', name: 'Close Short', mode: 'markers', yaxis: 'y',
        x: closeShort.map(s => new Date(s.t)), y: closeShort.map(s => s.p),
        marker: { symbol: 'x', size: 12, color: shortColors, line: { width: 2, color: 'white' } },
        customdata: closeShort.map(s => (s.ret ?? 0) * 100),
        text: closeShort.map(s => s.reason || ''),
        hovertemplate: '<b>Close Short</b><br>Price: %{y:.6f}<br>Return: %{customdata:.2f}%<br>Reason: %{text}<extra></extra>'
      };

      Plotly.react('chart', [candleTrace, emaTrace, lastPointTrace, buyTrace, shortTrace, closeLongTrace, closeShortTrace, macdTrace, signalTrace, histTrace], layout, { responsive: true });

      // Update ticker
      const ticker = document.getElementById('ticker');
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const localTime = new Date(payload.serverTime).toLocaleString(undefined, { hour12: false });
      ticker.textContent = `Last Price: ${lastPrice.toFixed(6)}  •  Updated: ${localTime}`;
    }

    async function refreshNow() {
      try {
        const data = await fetchCandles();
        if (data.success) displayChart(data);
      } catch (e) {
        console.error('Refresh error:', e);
      }
    }

    function start() {
      stop();
      refreshNow();
      const intervalMs = parseInt(document.getElementById('refreshMs').value) || 5000;
      pollHandle = setInterval(refreshNow, intervalMs);
      document.getElementById('startBtn').disabled = true;
      document.getElementById('stopBtn').disabled = false;
    }

    function stop() {
      if (pollHandle) clearInterval(pollHandle);
      pollHandle = null;
      document.getElementById('startBtn').disabled = false;
      document.getElementById('stopBtn').disabled = true;
    }

    window.onload = () => { start(); };
  </script>
</head>
<body>
  <div class="dashboard">
    <h1>📈 Live Candles + 200 EMA</h1>

    <div class="controls">
      <div class="control-group">
        <label>Symbol</label>
        <select id="symbol">
          <option value="BTCUSDT">BTCUSDT</option>
          <option value="ETHUSDT">ETHUSDT</option>
          <option value="BNBUSDT">BNBUSDT</option>
          <option value="SOLUSDT">SOLUSDT</option>
          <option value="ROSEUSDT" selected>ROSEUSDT</option>
          <option value="ADAUSDT">ADAUSDT</option>
          <option value="XRPUSDT">XRPUSDT</option>
          <option value="DOGEUSDT">DOGEUSDT</option>
        </select>
      </div>
      <div class="control-group">
        <label>Timeframe</label>
        <select id="interval">
          <option value="1m">1m</option>
          <option value="3m">3m</option>
          <option value="5m" selected>5m</option>
          <option value="15m">15m</option>
          <option value="30m">30m</option>
          <option value="1h">1h</option>
          <option value="2h">2h</option>
          <option value="4h">4h</option>
          <option value="1d">1d</option>
        </select>
      </div>
      <div class="control-group">
        <label>Limit</label>
        <input id="limit" type="number" value="300" min="100" max="1000" />
      </div>
      <div class="control-group">
        <label>Refresh (ms)</label>
        <input id="refreshMs" type="number" value="5000" min="1000" step="500" />
      </div>
      <button class="btn" id="startBtn" onclick="start()">Start</button>
      <button class="btn" id="stopBtn" onclick="stop()" disabled>Stop</button>
      <div class="ticker" id="ticker">Last Price: -</div>
    </div>

    <div id="chart"></div>
  </div>
</body>
</html>
"""


def get_client() -> Client:
    # Public market data works without API keys
    return Client()


@app.get("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.get("/api/live_klines")
def api_live_klines():
    try:
        symbol = request.args.get("symbol", "ROSEUSDT").upper()
        interval = request.args.get("interval", "5m")
        limit = int(request.args.get("limit", 300))

        client = get_client()
        # Use get_klines for recent candles
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        if not klines:
            return jsonify({"success": False, "error": "No data"}), 404

        # Parse data
        cols = ["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"]
        df = pd.DataFrame(klines, columns=cols)
        # Convert to Asia/Singapore timezone for client-side readability
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert("Asia/Singapore")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True).dt.tz_convert("Asia/Singapore")
        for c in ["open","high","low","close","volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        # Compute 200 EMA over close
        ema200_series = df["close"].ewm(span=200, adjust=False).mean()
        ema200 = ema200_series.tolist()

        # Compute MACD (12,26,9) on close
        close_s = df["close"].astype(float)
        ema_fast = close_s.ewm(span=12, adjust=False).mean()
        ema_slow = close_s.ewm(span=26, adjust=False).mean()
        macd = (ema_fast - ema_slow)
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal

        # Build signals using the same strategy rules
        macd_prev = macd.shift(1)
        signal_prev = signal.shift(1)
        bullish = (macd > signal) & (macd_prev <= signal_prev) & (macd < 0) & (signal < 0) & (df["close"] > ema200_series)
        bearish = (macd < signal) & (macd_prev >= signal_prev) & (macd > 0) & (signal > 0) & (df["close"] < ema200_series)

        buy_signals = []
        short_signals = []
        # Use candle close time to timestamp confirmed signals (bar-close confirmation)
        for t_close, c, bflag, sflag in zip(df["close_time"], df["close"], bullish, bearish):
            if bool(bflag):
                buy_signals.append({"t": t_close.isoformat(), "p": float(c)})
            if bool(sflag):
                short_signals.append({"t": t_close.isoformat(), "p": float(c)})

        # Backtest exits using TP/SL rules
        close_long = []
        close_short = []
        position = None
        entry_price = None
        entry_time = None
        for i in range(len(df)):
            # Attribute exits to the bar close time when the condition is reached
            t = df["close_time"].iloc[i]
            close_i = float(df["close"].iloc[i])
            high_i = float(df["high"].iloc[i])
            low_i = float(df["low"].iloc[i])

            if position is None:
                if bool(bullish.iloc[i]):
                    position = 'long'
                    entry_price = close_i
                    entry_time = t
                elif bool(bearish.iloc[i]):
                    position = 'short'
                    entry_price = close_i
                    entry_time = t
            elif position == 'long':
                tp = entry_price * (1 + TAKE_PROFIT)
                sl = entry_price * (1 - STOP_LOSS)
                if high_i >= tp:
                    close_long.append({"t": t.isoformat(), "p": tp, "ret": TAKE_PROFIT, "reason": "Take Profit"})
                    position = None
                elif low_i <= sl:
                    close_long.append({"t": t.isoformat(), "p": sl, "ret": -STOP_LOSS, "reason": "Stop Loss"})
                    position = None
            elif position == 'short':
                tp = entry_price * (1 - TAKE_PROFIT)
                sl = entry_price * (1 + STOP_LOSS)
                if low_i <= tp:
                    close_short.append({"t": t.isoformat(), "p": tp, "ret": TAKE_PROFIT, "reason": "Take Profit"})
                    position = None
                elif high_i >= sl:
                    close_short.append({"t": t.isoformat(), "p": sl, "ret": -STOP_LOSS, "reason": "Stop Loss"})
                    position = None

        candles = [
            {
                "t": t.isoformat(),
                "o": float(o),
                "h": float(h),
                "l": float(l),
                "c": float(c),
                "v": float(v),
            }
            for t, o, h, l, c, v in zip(
                df["open_time"], df["open"], df["high"], df["low"], df["close"], df["volume"]
            )
        ]

        payload = {
            "success": True,
            "symbol": symbol,
            "interval": interval,
            "candles": candles,
            "ema200": [float(x) if pd.notna(x) else None for x in ema200],
            "lastPrice": float(df["close"].iloc[-1]),
            "macd": [float(x) if pd.notna(x) else None for x in macd.tolist()],
            "signal": [float(x) if pd.notna(x) else None for x in signal.tolist()],
            "histogram": [float(x) if pd.notna(x) else None for x in histogram.tolist()],
            "buySignals": buy_signals,
            "shortSignals": short_signals,
            "closeLong": close_long,
            "closeShort": close_short,
            "serverTime": datetime.now(pytz.timezone("Asia/Singapore")).isoformat(),
        }
        
        # Telegram notifications for newest signals (avoid duplicates per symbol/interval/side)
        try:
            if buy_signals:
                last_buy = buy_signals[-1]
                key = (symbol, interval, 'BUY')
                if LAST_SENT_SIGNALS.get(key) != last_buy['t']:
                    # Freshness guard based on signal close_time
                    try:
                        now_dt = datetime.now(pytz.timezone("Asia/Singapore"))
                        sig_dt = pd.to_datetime(last_buy['t'])
                        if sig_dt.tzinfo is None:
                            sig_dt = pytz.timezone("Asia/Singapore").localize(sig_dt)
                        else:
                            sig_dt = sig_dt.tz_convert("Asia/Singapore")
                        age_sec = (now_dt - sig_dt).total_seconds()
                    except Exception:
                        age_sec = TELEGRAM_FRESH_MAX_AGE_SECONDS  # fail-safe: treat as stale
                    if 0 <= age_sec <= TELEGRAM_FRESH_MAX_AGE_SECONDS:
                        now_sgt = now_dt.strftime("%Y-%m-%d %H:%M SGT")
                        send_telegram_message(
                            f"✅ Buy Signal\nSymbol: <b>{symbol}</b>\nTF: <b>{interval}</b>\nPrice: <b>{last_buy['p']:.6f}</b>\nTime: <b>{format_sgt_time(last_buy['t'])}</b>\nSent: <b>{now_sgt}</b>"
                        )
                        LAST_SENT_SIGNALS[key] = last_buy['t']
            if short_signals:
                last_short = short_signals[-1]
                key = (symbol, interval, 'SHORT')
                if LAST_SENT_SIGNALS.get(key) != last_short['t']:
                    try:
                        now_dt = datetime.now(pytz.timezone("Asia/Singapore"))
                        sig_dt = pd.to_datetime(last_short['t'])
                        if sig_dt.tzinfo is None:
                            sig_dt = pytz.timezone("Asia/Singapore").localize(sig_dt)
                        else:
                            sig_dt = sig_dt.tz_convert("Asia/Singapore")
                        age_sec = (now_dt - sig_dt).total_seconds()
                    except Exception:
                        age_sec = TELEGRAM_FRESH_MAX_AGE_SECONDS
                    if 0 <= age_sec <= TELEGRAM_FRESH_MAX_AGE_SECONDS:
                        now_sgt = now_dt.strftime("%Y-%m-%d %H:%M SGT")
                        send_telegram_message(
                            f"⚠️ Short Signal\nSymbol: <b>{symbol}</b>\nTF: <b>{interval}</b>\nPrice: <b>{last_short['p']:.6f}</b>\nTime: <b>{format_sgt_time(last_short['t'])}</b>\nSent: <b>{now_sgt}</b>"
                        )
                        LAST_SENT_SIGNALS[key] = last_short['t']
        except Exception:
            pass

        return jsonify(payload)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.get("/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("🚀 Starting Live Candles + 200 EMA server at http://localhost:5001")
    app.run(debug=True, host="0.0.0.0", port=5001)


