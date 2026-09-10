import React, { useState, useEffect } from 'react';
import { useTheme, ThemeContextProvider } from './contexts/ThemeContext';
import { setAuthToken } from './api/apiClient';
import './App.css';

// Import Pages
import HomePage from './pages/HomePage';
import AboutUsPage from './pages/AboutUsPage';
import PdfChatPage from './pages/PdfChatPage';
import ContactUsPage from './pages/ContactUsPage';

// Import Common Components
import AppNavbar from './components/common/AppNavbar';
import LoginModal from './components/auth/LoginModal';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userName, setUserName] = useState('');
  const [userToken, setUserToken] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { theme } = useTheme();

  useEffect(() => {
      const storedToken = localStorage.getItem('userToken');
      const storedName = localStorage.getItem('userName');
      if (storedToken && storedName) {
          setIsLoggedIn(true);
          setUserName(storedName);
          setUserToken(storedToken);
          setAuthToken(storedToken);
      }
  }, []);

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
  }, [theme]);

  const handleLogin = (name, token) => {
    localStorage.setItem('userName', name);
    localStorage.setItem('userToken', token);
    setIsLoggedIn(true);
    setUserName(name);
    setUserToken(token);
    setAuthToken(token);
    setIsModalOpen(false);
  };
  
  const handleLogout = () => {
    localStorage.removeItem('userName');
    localStorage.removeItem('userToken');
    setIsLoggedIn(false);
    setUserName('');
    setUserToken('');
    setAuthToken(null);
    setCurrentPage('home');
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'chat':
        return isLoggedIn ? <PdfChatPage userToken={userToken} /> : <HomePage onNavigate={setCurrentPage} onLogin={handleLogin} isLoggedIn={isLoggedIn} userName={userName} />;
      case 'about':
        return <AboutUsPage onNavigate={setCurrentPage} />;
      case 'contact':
        return <ContactUsPage onNavigate={setCurrentPage} />;
      default:
        return <HomePage onNavigate={setCurrentPage} onLogin={handleLogin} isLoggedIn={isLoggedIn} userName={userName} />;
    }
  };

  return (
    <div>
       <style>{`
          @keyframes blink { 50% { opacity: 0; } }
          @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
      <LoginModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onLogin={handleLogin} />
      <AppNavbar
        onNavigate={setCurrentPage}
        isLoggedIn={isLoggedIn}
        onLogout={handleLogout}
        onLoginClick={() => setIsModalOpen(true)}
      />
      {renderPage()}
    </div>
  );
}

const AppWrapper = () => (
  <ThemeContextProvider>
    <App />
  </ThemeContextProvider>
);

export default AppWrapper;