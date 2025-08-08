import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

function MACDChart({ indicators, trades }) {
  const chartData = useMemo(() => {
    if (!indicators || !indicators.macd) return [];

    const traces = [];

    // MACD Line
    traces.push({
      x: indicators.macd.timestamps,
      y: indicators.macd.values,
      type: 'scatter',
      mode: 'lines',
      name: 'MACD',
      line: { color: '#2196F3', width: 2 }
    });

    // Signal Line
    traces.push({
      x: indicators.macd.timestamps,
      y: indicators.macd.signal,
      type: 'scatter',
      mode: 'lines',
      name: 'Signal',
      line: { color: '#FF5722', width: 2 }
    });

    // Histogram
    const histogramColors = indicators.macd.histogram.map(val => 
      val >= 0 ? '#00ff88' : '#ff4976'
    );

    traces.push({
      x: indicators.macd.timestamps,
      y: indicators.macd.histogram,
      type: 'bar',
      name: 'Histogram',
      marker: { color: histogramColors, opacity: 0.6 }
    });

    // Add crossover points if trades exist
    if (trades && trades.length > 0) {
      const crossoverPoints = trades.map(trade => {
        // Find the MACD value at entry time
        const entryIndex = indicators.macd.timestamps.findIndex(
          timestamp => new Date(timestamp).getTime() >= new Date(trade.entry_date).getTime()
        );
        
        if (entryIndex >= 0) {
          return {
            x: trade.entry_date,
            y: indicators.macd.values[entryIndex]
          };
        }
        return null;
      }).filter(Boolean);

      if (crossoverPoints.length > 0) {
        traces.push({
          x: crossoverPoints.map(p => p.x),
          y: crossoverPoints.map(p => p.y),
          type: 'scatter',
          mode: 'markers',
          name: 'MACD Crossover',
          marker: {
            symbol: 'circle',
            size: 8,
            color: '#00ff88',
            line: { color: 'white', width: 2 }
          },
          showlegend: false
        });
      }
    }

    return traces;
  }, [indicators, trades]);

  const layout = {
    title: {
      text: 'MACD Indicator',
      font: { color: '#ffffff', size: 14 }
    },
    plot_bgcolor: '#131722',
    paper_bgcolor: '#131722',
    font: { color: '#ffffff' },
    xaxis: {
      gridcolor: '#363C4E',
      showgrid: true,
      zeroline: false,
      type: 'date'
    },
    yaxis: {
      gridcolor: '#363C4E',
      showgrid: true,
      zeroline: true,
      zerolinecolor: 'white',
      zerolinewidth: 1
    },
    legend: {
      orientation: 'h',
      y: 1.02,
      x: 0,
      bgcolor: 'rgba(0,0,0,0)',
      font: { color: '#ffffff', size: 10 }
    },
    margin: { l: 40, r: 40, t: 40, b: 40 },
    autosize: true,
    shapes: [
      {
        type: 'line',
        x0: indicators?.macd?.timestamps[0],
        x1: indicators?.macd?.timestamps[indicators.macd.timestamps.length - 1],
        y0: 0,
        y1: 0,
        line: {
          color: 'white',
          width: 1,
          dash: 'dash'
        }
      }
    ]
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

export default MACDChart;
