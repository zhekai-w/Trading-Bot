import React from 'react';
import styled from 'styled-components';
import { TrendingUp, TrendingDown, DollarSign, Clock, BarChart3 } from 'lucide-react';

const TradesContainer = styled.div`
  height: 100%;
  overflow-y: auto;
`;

const TradesListContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const TradeItem = styled.div`
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 12px;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--blue);
    transform: translateX(4px);
  }
`;

const TradeHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

const TradeReturn = styled.div`
  font-weight: bold;
  font-size: 14px;
  color: ${props => props.isProfit ? 'var(--green)' : 'var(--red)'};
  display: flex;
  align-items: center;
  gap: 4px;
`;

const TradeReason = styled.div`
  font-size: 12px;
  color: var(--text-secondary);
  background-color: ${props => props.isProfit ? 'rgba(0, 255, 136, 0.1)' : 'rgba(255, 73, 118, 0.1)'};
  padding: 2px 6px;
  border-radius: 4px;
`;

const TradeDetails = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  font-size: 11px;
  color: var(--text-secondary);
`;

const DetailItem = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
`;

const PriceChange = styled.span`
  color: ${props => props.isProfit ? 'var(--green)' : 'var(--red)'};
  font-weight: 500;
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-secondary);
  text-align: center;
`;

function TradesList({ trades }) {
  if (!trades || trades.length === 0) {
    return (
      <TradesContainer>
        <EmptyState>
          <BarChart3 size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
          <h3>No Trades Yet</h3>
          <p>Run a backtest to see trading results</p>
        </EmptyState>
      </TradesContainer>
    );
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatPrice = (price) => {
    return parseFloat(price).toFixed(6);
  };

  const formatPercent = (value) => {
    const percent = value * 100;
    return `${percent > 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  // Show last 20 trades, most recent first
  const recentTrades = trades.slice(-20).reverse();

  return (
    <TradesContainer>
      <TradesListContainer>
        {recentTrades.map((trade, index) => {
          const isProfit = trade.return_pct > 0;
          const priceChange = trade.exit_price - trade.entry_price;
          
          return (
            <TradeItem key={index}>
              <TradeHeader>
                <TradeReturn isProfit={isProfit}>
                  {isProfit ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  {formatPercent(trade.return_pct)}
                </TradeReturn>
                <TradeReason isProfit={isProfit}>
                  {trade.exit_reason}
                </TradeReason>
              </TradeHeader>
              
              <TradeDetails>
                <DetailItem>
                  <Clock size={10} />
                  Entry: {formatDate(trade.entry_date)}
                </DetailItem>
                <DetailItem>
                  <Clock size={10} />
                  Exit: {formatDate(trade.exit_date)}
                </DetailItem>
                <DetailItem>
                  <DollarSign size={10} />
                  Entry: {formatPrice(trade.entry_price)}
                </DetailItem>
                <DetailItem>
                  <DollarSign size={10} />
                  Exit: {formatPrice(trade.exit_price)}
                </DetailItem>
              </TradeDetails>
              
              <div style={{ 
                marginTop: '8px', 
                fontSize: '11px', 
                textAlign: 'center',
                color: 'var(--text-secondary)'
              }}>
                Change: <PriceChange isProfit={isProfit}>
                  {priceChange > 0 ? '+' : ''}{priceChange.toFixed(6)}
                </PriceChange>
              </div>
            </TradeItem>
          );
        })}
      </TradesListContainer>
    </TradesContainer>
  );
}

export default TradesList;
