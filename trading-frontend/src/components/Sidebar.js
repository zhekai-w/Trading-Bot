import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  TrendingUp, 
  BarChart3, 
  Settings, 
  Zap, 
  DollarSign,
  Clock,
  Target,
  Shield
} from 'lucide-react';

const SidebarContainer = styled.aside`
  width: ${props => props.isOpen ? '280px' : '0px'};
  background-color: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  transition: width 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const SidebarContent = styled.div`
  padding: 24px;
  min-width: 280px;
`;

const Section = styled.div`
  margin-bottom: 32px;
`;

const SectionTitle = styled.h3`
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 16px;
`;

const ControlGroup = styled.div`
  margin-bottom: 20px;
`;

const Label = styled.label`
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 6px;
`;

const Select = styled.select`
  width: 100%;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: var(--blue);
  }

  option {
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
  }
`;

const Input = styled.input`
  width: 100%;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;

  &:focus {
    outline: none;
    border-color: var(--blue);
  }
`;

const Button = styled.button`
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 8px;

  &.primary {
    background-color: var(--blue);
    color: white;
    
    &:hover {
      background-color: #1976d2;
    }
  }

  &.success {
    background-color: var(--green);
    color: black;
    
    &:hover {
      background-color: #00e676;
    }
  }

  &.danger {
    background-color: var(--red);
    color: white;
    
    &:hover {
      background-color: #f44336;
    }
  }
`;

const MetricCard = styled.div`
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
`;

const MetricHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
`;

const MetricValue = styled.div`
  font-size: 20px;
  font-weight: bold;
  color: ${props => {
    if (props.type === 'positive') return 'var(--green)';
    if (props.type === 'negative') return 'var(--red)';
    return 'var(--text-primary)';
  }};
`;

function Sidebar({ isOpen }) {
  const [symbol, setSymbol] = useState('ROSEUSDT');
  const [interval, setInterval] = useState('5m');
  const [daysBack, setDaysBack] = useState(7);
  const [takeProfit, setTakeProfit] = useState(2.0);
  const [stopLoss, setStopLoss] = useState(1.0);

  const symbols = [
    'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT',
    'LTCUSDT', 'BCHUSDT', 'XLMUSDT', 'EOSUSDT', 'TRXUSDT',
    'ROSEUSDT', 'SOLUSDT', 'AVAXUSDT', 'MATICUSDT', 'UNIUSDT'
  ];

  const intervals = [
    { value: '1m', label: '1 Minute' },
    { value: '3m', label: '3 Minutes' },
    { value: '5m', label: '5 Minutes' },
    { value: '15m', label: '15 Minutes' },
    { value: '30m', label: '30 Minutes' },
    { value: '1h', label: '1 Hour' },
    { value: '4h', label: '4 Hours' },
    { value: '1d', label: '1 Day' }
  ];

  return (
    <SidebarContainer isOpen={isOpen}>
      <SidebarContent>
        <Section>
          <SectionTitle>Trading Configuration</SectionTitle>
          
          <ControlGroup>
            <Label>Symbol</Label>
            <Select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {symbols.map(sym => (
                <option key={sym} value={sym}>{sym}</option>
              ))}
            </Select>
          </ControlGroup>

          <ControlGroup>
            <Label>Timeframe</Label>
            <Select value={interval} onChange={(e) => setInterval(e.target.value)}>
              {intervals.map(int => (
                <option key={int.value} value={int.value}>{int.label}</option>
              ))}
            </Select>
          </ControlGroup>

          <ControlGroup>
            <Label>Days Back</Label>
            <Input 
              type="number" 
              value={daysBack} 
              onChange={(e) => setDaysBack(Number(e.target.value))}
              min="1"
              max="365"
            />
          </ControlGroup>
        </Section>

        <Section>
          <SectionTitle>Risk Management</SectionTitle>
          
          <ControlGroup>
            <Label>Take Profit (%)</Label>
            <Input 
              type="number" 
              value={takeProfit} 
              onChange={(e) => setTakeProfit(Number(e.target.value))}
              step="0.1"
              min="0.1"
              max="10"
            />
          </ControlGroup>

          <ControlGroup>
            <Label>Stop Loss (%)</Label>
            <Input 
              type="number" 
              value={stopLoss} 
              onChange={(e) => setStopLoss(Number(e.target.value))}
              step="0.1"
              min="0.1"
              max="5"
            />
          </ControlGroup>
        </Section>

        <Section>
          <SectionTitle>Actions</SectionTitle>
          
          <Button className="primary">
            <BarChart3 size={16} style={{ marginRight: '8px', display: 'inline' }} />
            Run Backtest
          </Button>
          
          <Button className="success">
            <Zap size={16} style={{ marginRight: '8px', display: 'inline' }} />
            Start Live Trading
          </Button>
          
          <Button className="danger">
            <Shield size={16} style={{ marginRight: '8px', display: 'inline' }} />
            Stop All Positions
          </Button>
        </Section>

        <Section>
          <SectionTitle>Quick Stats</SectionTitle>
          
          <MetricCard>
            <MetricHeader>
              <DollarSign size={14} />
              Total Return
            </MetricHeader>
            <MetricValue type="positive">+22.03%</MetricValue>
          </MetricCard>

          <MetricCard>
            <MetricHeader>
              <Target size={14} />
              Win Rate
            </MetricHeader>
            <MetricValue>47.92%</MetricValue>
          </MetricCard>

          <MetricCard>
            <MetricHeader>
              <TrendingUp size={14} />
              Total Trades
            </MetricHeader>
            <MetricValue>134</MetricValue>
          </MetricCard>

          <MetricCard>
            <MetricHeader>
              <Clock size={14} />
              Active Time
            </MetricHeader>
            <MetricValue>90 days</MetricValue>
          </MetricCard>
        </Section>
      </SidebarContent>
    </SidebarContainer>
  );
}

export default Sidebar;
