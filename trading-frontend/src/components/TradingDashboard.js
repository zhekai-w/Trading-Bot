import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import CandlestickChart from './CandlestickChart';
import MACDChart from './MACDChart';
import PerformanceMetrics from './PerformanceMetrics';
import TradesList from './TradesList';
import { useTradingData } from '../hooks/useTradingData';

const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  gap: 24px;
  overflow-y: auto;
`;

const ChartsRow = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  height: 60vh;
`;

const ChartContainer = styled.div`
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const ChartTitle = styled.h3`
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ChartContent = styled.div`
  flex: 1;
  position: relative;
`;

const BottomRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  height: 35vh;
`;

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-secondary);
`;

const ErrorContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--red);
  text-align: center;
`;

function TradingDashboard() {
  const [symbol, setSymbol] = useState('ROSEUSDT');
  const [interval, setInterval] = useState('5m');
  const [daysBack, setDaysBack] = useState(7);
  
  const { 
    data, 
    indicators, 
    trades, 
    performance, 
    loading, 
    error, 
    fetchData,
    runBacktest 
  } = useTradingData();

  useEffect(() => {
    // Fetch initial data
    fetchData(symbol, interval, daysBack);
  }, [symbol, interval, daysBack]);

  const handleRunBacktest = async () => {
    try {
      await runBacktest(symbol, interval, {
        days_back: daysBack,
        take_profit: 0.02,
        stop_loss: 0.01,
        fast_length: 12,
        slow_length: 26,
        signal_smoothing: 9
      });
    } catch (err) {
      console.error('Backtest failed:', err);
    }
  };

  if (loading) {
    return (
      <DashboardContainer>
        <LoadingContainer>
          <div>
            <div className="spinner"></div>
            <p style={{ marginTop: '16px' }}>Loading trading data...</p>
          </div>
        </LoadingContainer>
      </DashboardContainer>
    );
  }

  if (error) {
    return (
      <DashboardContainer>
        <ErrorContainer>
          <div>
            <h3>Error Loading Data</h3>
            <p>{error}</p>
            <button 
              className="btn btn-primary" 
              onClick={() => fetchData(symbol, interval, daysBack)}
              style={{ marginTop: '16px' }}
            >
              Retry
            </button>
          </div>
        </ErrorContainer>
      </DashboardContainer>
    );
  }

  return (
    <DashboardContainer>
      <ChartsRow>
        <ChartContainer>
          <ChartTitle>
            {symbol} Price Chart - {interval} | 200 EMA + MACD Strategy
          </ChartTitle>
          <ChartContent>
            {data && indicators ? (
              <CandlestickChart 
                data={data} 
                indicators={indicators}
                trades={trades}
                symbol={symbol}
                interval={interval}
              />
            ) : (
              <LoadingContainer>
                <div className="spinner"></div>
              </LoadingContainer>
            )}
          </ChartContent>
        </ChartContainer>
      </ChartsRow>

      <BottomRow>
        <ChartContainer>
          <ChartTitle>
            MACD Indicator
          </ChartTitle>
          <ChartContent>
            {indicators ? (
              <MACDChart 
                indicators={indicators}
                trades={trades}
              />
            ) : (
              <LoadingContainer>
                <div className="spinner"></div>
              </LoadingContainer>
            )}
          </ChartContent>
        </ChartContainer>

        <ChartContainer>
          <ChartTitle>
            Performance Metrics
          </ChartTitle>
          <ChartContent>
            {performance ? (
              <PerformanceMetrics 
                performance={performance}
                trades={trades}
              />
            ) : (
              <LoadingContainer>
                <div className="spinner"></div>
              </LoadingContainer>
            )}
          </ChartContent>
        </ChartContainer>
      </BottomRow>
    </DashboardContainer>
  );
}

export default TradingDashboard;
