import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import TradingDashboard from './components/TradingDashboard';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import { TradingProvider } from './context/TradingContext';
import './App.css';

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
`;

const MainContent = styled.div`
  display: flex;
  flex: 1;
  overflow: hidden;
`;

const ContentArea = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <TradingProvider>
      <AppContainer>
        <Header 
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />
        <MainContent>
          <Sidebar isOpen={sidebarOpen} />
          <ContentArea>
            <TradingDashboard />
          </ContentArea>
        </MainContent>
      </AppContainer>
    </TradingProvider>
  );
}

export default App;
