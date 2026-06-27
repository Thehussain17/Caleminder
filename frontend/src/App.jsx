import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getAuthStatus } from './api/client';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import './index.css';

function App() {
  const [auth, setAuth] = useState(null); // null = loading

  useEffect(() => {
    getAuthStatus().then(data => {
      setAuth(data.authenticated ? data : { authenticated: false });
    });
  }, []);

  if (auth === null) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#050508' }}>
        <span className="pixel-text neon-text" style={{ fontSize: '0.7rem' }}>LOADING...</span>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div className="scanline-overlay" />
      <div className="crt-vignette" />
      <Routes>
        <Route path="/login" element={
          auth.authenticated ? <Navigate to="/" /> : <LoginPage />
        } />
        <Route path="/chat/:sessionId" element={
          auth.authenticated ? <ChatPage user={auth.user} setAuth={setAuth} /> : <Navigate to="/login" />
        } />
        <Route path="/" element={
          auth.authenticated ? <ChatPage user={auth.user} setAuth={setAuth} /> : <Navigate to="/login" />
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
