import React, { createContext, useContext, useReducer } from 'react';

// Initial state
const initialState = {
  // Market data
  data: null,
  indicators: null,
  trades: null,
  performance: null,
  
  // UI state
  loading: false,
  error: null,
  
  // Trading state
  isConnected: false,
  isLiveTrading: false,
  
  // Configuration
  symbol: 'ROSEUSDT',
  interval: '5m',
  daysBack: 7,
  
  // Strategy parameters
  takeProfit: 2.0,
  stopLoss: 1.0,
  fastLength: 12,
  slowLength: 26,
  signalSmoothing: 9
};

// Action types
const actionTypes = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_DATA: 'SET_DATA',
  SET_INDICATORS: 'SET_INDICATORS',
  SET_TRADES: 'SET_TRADES',
  SET_PERFORMANCE: 'SET_PERFORMANCE',
  SET_CONNECTION_STATUS: 'SET_CONNECTION_STATUS',
  SET_LIVE_TRADING: 'SET_LIVE_TRADING',
  UPDATE_CONFIG: 'UPDATE_CONFIG',
  UPDATE_STRATEGY_PARAMS: 'UPDATE_STRATEGY_PARAMS',
  CLEAR_DATA: 'CLEAR_DATA'
};

// Reducer
function tradingReducer(state, action) {
  switch (action.type) {
    case actionTypes.SET_LOADING:
      return { ...state, loading: action.payload, error: null };
    
    case actionTypes.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
    
    case actionTypes.SET_DATA:
      return { ...state, data: action.payload, loading: false, error: null };
    
    case actionTypes.SET_INDICATORS:
      return { ...state, indicators: action.payload };
    
    case actionTypes.SET_TRADES:
      return { ...state, trades: action.payload };
    
    case actionTypes.SET_PERFORMANCE:
      return { ...state, performance: action.payload };
    
    case actionTypes.SET_CONNECTION_STATUS:
      return { ...state, isConnected: action.payload };
    
    case actionTypes.SET_LIVE_TRADING:
      return { ...state, isLiveTrading: action.payload };
    
    case actionTypes.UPDATE_CONFIG:
      return { ...state, ...action.payload };
    
    case actionTypes.UPDATE_STRATEGY_PARAMS:
      return { ...state, ...action.payload };
    
    case actionTypes.CLEAR_DATA:
      return {
        ...state,
        data: null,
        indicators: null,
        trades: null,
        performance: null,
        error: null
      };
    
    default:
      return state;
  }
}

// Context
const TradingContext = createContext();

// Provider component
export function TradingProvider({ children }) {
  const [state, dispatch] = useReducer(tradingReducer, initialState);

  // Actions
  const setLoading = (loading) => {
    dispatch({ type: actionTypes.SET_LOADING, payload: loading });
  };

  const setError = (error) => {
    dispatch({ type: actionTypes.SET_ERROR, payload: error });
  };

  const setData = (data) => {
    dispatch({ type: actionTypes.SET_DATA, payload: data });
  };

  const setIndicators = (indicators) => {
    dispatch({ type: actionTypes.SET_INDICATORS, payload: indicators });
  };

  const setTrades = (trades) => {
    dispatch({ type: actionTypes.SET_TRADES, payload: trades });
  };

  const setPerformance = (performance) => {
    dispatch({ type: actionTypes.SET_PERFORMANCE, payload: performance });
  };

  const setConnectionStatus = (isConnected) => {
    dispatch({ type: actionTypes.SET_CONNECTION_STATUS, payload: isConnected });
  };

  const setLiveTrading = (isLiveTrading) => {
    dispatch({ type: actionTypes.SET_LIVE_TRADING, payload: isLiveTrading });
  };

  const updateConfig = (config) => {
    dispatch({ type: actionTypes.UPDATE_CONFIG, payload: config });
  };

  const updateStrategyParams = (params) => {
    dispatch({ type: actionTypes.UPDATE_STRATEGY_PARAMS, payload: params });
  };

  const clearData = () => {
    dispatch({ type: actionTypes.CLEAR_DATA });
  };

  const value = {
    // State
    ...state,
    
    // Actions
    setLoading,
    setError,
    setData,
    setIndicators,
    setTrades,
    setPerformance,
    setConnectionStatus,
    setLiveTrading,
    updateConfig,
    updateStrategyParams,
    clearData
  };

  return (
    <TradingContext.Provider value={value}>
      {children}
    </TradingContext.Provider>
  );
}

// Hook to use the trading context
export function useTradingContext() {
  const context = useContext(TradingContext);
  if (!context) {
    throw new Error('useTradingContext must be used within a TradingProvider');
  }
  return context;
}

export default TradingContext;
