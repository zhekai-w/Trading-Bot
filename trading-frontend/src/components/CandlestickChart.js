import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

function CandlestickChart({ data, indicators, trades, symbol, interval }) {
  const chartData = useMemo(() => {
    if (!data || !indicators) return [];

    const traces = [];

    // Candlestick trace
    traces.push({
      x: data.timestamps,
      open: data.ohlcv.map(d => d.Open),
      high: data.ohlcv.map(d => d.High),
      low: data.ohlcv.map(d => d.Low),
      close: data.ohlcv.map(d => d.Close),
      type: 'candlestick',
      name: 'Price',
      increasing: { line: { color: '#00ff88' } },
      decreasing: { line: { color: '#ff4976' } },
      xaxis: 'x',
      yaxis: 'y'
    });

    // 200 EMA trace
    if (indicators.ema_200 && indicators.ema_200.values.length > 0) {
      traces.push({
        x: indicators.ema_200.timestamps,
        y: indicators.ema_200.values,
        type: 'scatter',
        mode: 'lines',
        name: '200 EMA',
        line: { color: '#FFD700', width: 2 },
        xaxis: 'x',
        yaxis: 'y'
      });
    }

    // Buy signals
    if (trades && trades.length > 0) {
      const entryPoints = trades.map(trade => ({
        x: trade.entry_date,
        y: trade.entry_price,
        text: `Entry: $${trade.entry_price.toFixed(6)}`,
        mode: 'markers',
        marker: {
          symbol: 'triangle-up',
          size: 12,
          color: '#00ff88',
          line: { color: 'white', width: 2 }
        }
      }));

      if (entryPoints.length > 0) {
        traces.push({
          x: entryPoints.map(p => p.x),
          y: entryPoints.map(p => p.y),
          type: 'scatter',
          mode: 'markers',
          name: 'Buy Signals',
          marker: {
            symbol: 'triangle-up',
            size: 12,
            color: '#00ff88',
            line: { color: 'white', width: 2 }
          },
          xaxis: 'x',
          yaxis: 'y'
        });
      }

      // Exit signals
      const exitPoints = trades.map(trade => ({
        x: trade.exit_date,
        y: trade.exit_price,
        return_pct: trade.return_pct,
        exit_reason: trade.exit_reason
      }));

      if (exitPoints.length > 0) {
        traces.push({
          x: exitPoints.map(p => p.x),
          y: exitPoints.map(p => p.y),
          type: 'scatter',
          mode: 'markers',
          name: 'Exit Signals',
          marker: {
            symbol: 'triangle-down',
            size: 10,
            color: exitPoints.map(p => p.return_pct > 0 ? '#00ff88' : '#ff4976'),
            line: { color: 'white', width: 2 }
          },
          text: exitPoints.map(p => 
            `${p.exit_reason}<br>Return: ${(p.return_pct * 100).toFixed(2)}%`
          ),
          hovertemplate: '%{text}<br>Price: %{y:.6f}<br>Date: %{x}<extra></extra>',
          xaxis: 'x',
          yaxis: 'y'
        });
      }
    }

    return traces;
  }, [data, indicators, trades]);

  const layout = {
    title: {
      text: `${symbol} - ${interval} Chart`,
      font: { color: '#ffffff', size: 16 }
    },
    plot_bgcolor: '#131722',
    paper_bgcolor: '#131722',
    font: { color: '#ffffff' },
    xaxis: {
      gridcolor: '#363C4E',
      showgrid: true,
      zeroline: false,
      rangeslider: { visible: false },
      type: 'date'
    },
    yaxis: {
      gridcolor: '#363C4E',
      showgrid: true,
      zeroline: false,
      side: 'right'
    },
    legend: {
      orientation: 'h',
      y: 1.02,
      x: 0,
      bgcolor: 'rgba(0,0,0,0)',
      font: { color: '#ffffff' }
    },
    margin: { l: 50, r: 50, t: 50, b: 50 },
    autosize: true
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: [
      'pan2d',
      'lasso2d',
      'select2d',
      'autoScale2d',
      'hoverClosestCartesian',
      'hoverCompareCartesian'
    ]
  };

  return (
    <Plot
      data={chartData}
      layout={layout}
      config={config}
      style={{ width: '100%', height: '100%' }}
      useResizeHandler={true}
    />
  );
}

export default CandlestickChart;
