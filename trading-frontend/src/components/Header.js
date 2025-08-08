import React from 'react';
import styled from 'styled-components';
import { BarChart3, Settings, Activity } from 'lucide-react';

const HeaderContainer = styled.header`
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: bold;
  color: var(--text-primary);
`;

const LogoIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--blue), var(--purple));
  border-radius: 8px;
`;

const Nav = styled.nav`
  display: flex;
  gap: 24px;
  align-items: center;
`;

const NavItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  color: var(--text-secondary);
  font-size: 14px;

  &:hover {
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
  }

  &.active {
    background-color: var(--blue);
    color: white;
  }
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  background-color: var(--bg-tertiary);
  font-size: 12px;
  color: var(--text-secondary);
`;

const StatusDot = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: ${props => props.connected ? 'var(--green)' : 'var(--red)'};
`;

function Header({ onToggleSidebar }) {
  return (
    <HeaderContainer>
      <Logo>
        <LogoIcon>
          <BarChart3 size={20} color="white" />
        </LogoIcon>
        Trading Dashboard
      </Logo>
      
      <Nav>
        <NavItem className="active">
          <Activity size={16} />
          Live Trading
        </NavItem>
        <NavItem>
          <Settings size={16} />
          Settings
        </NavItem>
        
        <StatusIndicator>
          <StatusDot connected={true} />
          API Connected
        </StatusIndicator>
      </Nav>
    </HeaderContainer>
  );
}

export default Header;
