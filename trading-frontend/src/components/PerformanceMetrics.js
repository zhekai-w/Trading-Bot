import React from 'react';
import styled from 'styled-components';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  DollarSign,
  BarChart3,
  Shield,
  Clock,
  Zap
} from 'lucide-react';

const MetricsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  height: 100%;
  overflow-y: auto;
`;

const MetricCard = styled.div`
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: transform 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    border-color: var(--blue);
  }
`;

const MetricIcon = styled.div`
  margin-bottom: 8px;
  color: ${props => {
    if (props.type === 'positive') return 'var(--green)';
    if (props.type === 'negative') return 'var(--red)';
    if (props.type === 'warning') return 'var(--orange)';
    return 'var(--blue)';
  }};
`;

const MetricValue = styled.div`
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 4px;
  color: ${props => {
    if (props.type === 'positive') return 'var(--green)';
    if (props.type === 'negative') return 'var(--red)';
    return 'var(--text-primary)';
  }};
`;

const MetricLabel = styled.div`
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
`;

const SummaryCard = styled.div`
  grid-column: 1 / -1;
  background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
`;

const SummaryTitle = styled.h3`
  color: var(--text-primary);
  font-size: 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const SummaryStats = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
`;

const StatItem = styled.div`
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 18px;
  font-weight: bold;
  color: ${props => {
    if (props.type === 'positive') return 'var(--green)';
    if (props.type === 'negative') return 'var(--red)';
    return 'var(--text-primary)';
  }};
`;

const StatLabel = styled.div`
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 4px;
`;

function PerformanceMetrics({ performance, trades }) {
  if (!performance) {
    return (
      <MetricsContainer>
        <div style={{ gridColumn: '1 / -1', textAlign: 'center', color: 'var(--text-secondary)' }}>
          No performance data available
        </div>
      </MetricsContainer>
    );
  }

  const formatPercent = (value) => `${value.toFixed(2)}%`;
  const formatNumber = (value) => value.toString();

  const getMetricType = (value, threshold = 0) => {
    if (value > threshold) return 'positive';
    if (value < threshold) return 'negative';
    return 'neutral';
  };

  return (
    <MetricsContainer>
      <SummaryCard>
        <SummaryTitle>
          <BarChart3 size={16} />
          Strategy Performance Summary
        </SummaryTitle>
        <SummaryStats>
          <StatItem>
            <StatValue type={getMetricType(performance.total_return)}>
              {formatPercent(performance.total_return)}
            </StatValue>
            <StatLabel>Total Return</StatLabel>
          </StatItem>
          <StatItem>
            <StatValue type={getMetricType(performance.win_rate, 50)}>
              {formatPercent(performance.win_rate)}
            </StatValue>
            <StatLabel>Win Rate</StatLabel>
          </StatItem>
          <StatItem>
            <StatValue>
              {formatNumber(performance.total_trades)}
            </StatValue>
            <StatLabel>Total Trades</StatLabel>
          </StatItem>
          <StatItem>
            <StatValue type={getMetricType(performance.sharpe_ratio, 1)}>
              {performance.sharpe_ratio.toFixed(2)}
            </StatValue>
            <StatLabel>Sharpe Ratio</StatLabel>
          </StatItem>
        </SummaryStats>
      </SummaryCard>

      <MetricCard>
        <MetricIcon type={getMetricType(performance.total_return)}>
          <DollarSign size={20} />
        </MetricIcon>
        <MetricValue type={getMetricType(performance.total_return)}>
          {formatPercent(performance.total_return)}
        </MetricValue>
        <MetricLabel>Total Return</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon type={getMetricType(performance.win_rate, 50)}>
          <Target size={20} />
        </MetricIcon>
        <MetricValue type={getMetricType(performance.win_rate, 50)}>
          {formatPercent(performance.win_rate)}
        </MetricValue>
        <MetricLabel>Win Rate</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon>
          <BarChart3 size={20} />
        </MetricIcon>
        <MetricValue>
          {formatNumber(performance.total_trades)}
        </MetricValue>
        <MetricLabel>Total Trades</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon type="positive">
          <TrendingUp size={20} />
        </MetricIcon>
        <MetricValue type="positive">
          {formatNumber(performance.winning_trades)}
        </MetricValue>
        <MetricLabel>Winning Trades</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon type="negative">
          <TrendingDown size={20} />
        </MetricIcon>
        <MetricValue type="negative">
          {formatNumber(performance.losing_trades)}
        </MetricValue>
        <MetricLabel>Losing Trades</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon type={getMetricType(performance.average_return)}>
          <Zap size={20} />
        </MetricIcon>
        <MetricValue type={getMetricType(performance.average_return)}>
          {formatPercent(performance.average_return)}
        </MetricValue>
        <MetricLabel>Avg Return</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon type="positive">
          <TrendingUp size={20} />
        </MetricIcon>
        <MetricValue type="positive">
          {formatPercent(performance.best_trade)}
        </MetricValue>
        <MetricLabel>Best Trade</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon type="negative">
          <TrendingDown size={20} />
        </MetricIcon>
        <MetricValue type="negative">
          {formatPercent(performance.worst_trade)}
        </MetricValue>
        <MetricLabel>Worst Trade</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon type={getMetricType(-performance.max_drawdown, -10)}>
          <Shield size={20} />
        </MetricIcon>
        <MetricValue type={getMetricType(-performance.max_drawdown, -10)}>
          {formatPercent(performance.max_drawdown)}
        </MetricValue>
        <MetricLabel>Max Drawdown</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon>
          <Target size={20} />
        </MetricIcon>
        <MetricValue>
          {formatNumber(performance.take_profit_hits)}
        </MetricValue>
        <MetricLabel>Take Profits</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon>
          <Shield size={20} />
        </MetricIcon>
        <MetricValue>
          {formatNumber(performance.stop_loss_hits)}
        </MetricValue>
        <MetricLabel>Stop Losses</MetricLabel>
      </MetricCard>

      <MetricCard>
        <MetricIcon type={getMetricType(performance.sharpe_ratio, 1)}>
          <Clock size={20} />
        </MetricIcon>
        <MetricValue type={getMetricType(performance.sharpe_ratio, 1)}>
          {performance.sharpe_ratio.toFixed(2)}
        </MetricValue>
        <MetricLabel>Sharpe Ratio</MetricLabel>
      </MetricCard>
    </MetricsContainer>
  );
}

export default PerformanceMetrics;
