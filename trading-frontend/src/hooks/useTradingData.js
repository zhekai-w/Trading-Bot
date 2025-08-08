import { useState, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export function useTradingData() {
  const [data, setData] = useState(null);
  const [indicators, setIndicators] = useState(null);
  const [trades, setTrades] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (symbol, interval, daysBack = 7, timezone = 'Asia/Singapore') => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/data/${symbol}/${interval}`,
        {
          params: {
            days: daysBack,
            timezone: timezone
          }
        }
      );

      if (response.data.success) {
        setData(response.data.data);
        setIndicators(response.data.indicators);
      } else {
        throw new Error(response.data.error || 'Failed to fetch data');
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.response?.data?.error || err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, []);

  const runBacktest = useCallback(async (symbol, interval, config) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/backtest/${symbol}/${interval}`,
        {
          days_back: config.days_back || 7,
          timezone: config.timezone || 'Asia/Singapore',
          take_profit: config.take_profit || 0.02,
          stop_loss: config.stop_loss || 0.01,
          fast_length: config.fast_length || 12,
          slow_length: config.slow_length || 26,
          signal_smoothing: config.signal_smoothing || 9
        },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data.success) {
        const results = response.data.results;
        setTrades(results.trades || []);
        setPerformance(results.performance || null);
        return results;
      } else {
        throw new Error(response.data.error || 'Backtest failed');
      }
    } catch (err) {
      console.error('Error running backtest:', err);
      setError(err.response?.data?.error || err.message || 'Backtest failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const startRealTimeStream = useCallback(async (symbol, interval, timezone = 'Asia/Singapore') => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/stream/start`,
        {
          symbol,
          interval,
          timezone
        },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to start stream');
      }

      return response.data;
    } catch (err) {
      console.error('Error starting stream:', err);
      setError(err.response?.data?.error || err.message || 'Failed to start stream');
      throw err;
    }
  }, []);

  const stopRealTimeStream = useCallback(async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/stream/stop`);
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to stop stream');
      }

      return response.data;
    } catch (err) {
      console.error('Error stopping stream:', err);
      setError(err.response?.data?.error || err.message || 'Failed to stop stream');
      throw err;
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/health`);
      return response.data;
    } catch (err) {
      console.error('Health check failed:', err);
      throw err;
    }
  }, []);

  const getSymbols = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/symbols`);
      return response.data.symbols || [];
    } catch (err) {
      console.error('Error fetching symbols:', err);
      return [];
    }
  }, []);

  const getIntervals = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/intervals`);
      return response.data.intervals || [];
    } catch (err) {
      console.error('Error fetching intervals:', err);
      return [];
    }
  }, []);

  return {
    // State
    data,
    indicators,
    trades,
    performance,
    loading,
    error,
    
    // Actions
    fetchData,
    runBacktest,
    startRealTimeStream,
    stopRealTimeStream,
    checkHealth,
    getSymbols,
    getIntervals,
    
    // Setters for external updates
    setData,
    setIndicators,
    setTrades,
    setPerformance,
    setError
  };
}
