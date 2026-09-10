import React, { useState } from 'react';
import LoginModal from '../components/auth/LoginModal';
import Footer from '../components/common/Footer';
import { ChatIcon, DocumentIcon, ConnectIcon } from '../components/common/Icons'; // Assuming you add these to Icons.js

const HomePage = ({ onNavigate, onLogin, isLoggedIn, userName }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleLaunchClick = () => {
    if (isLoggedIn) {
      onNavigate('chat');
    } else {
      setIsModalOpen(true);
    }
  };

  return (
    <div className="page-container">
      <LoginModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onLogin={onLogin} />
      
      <header className="hero-parallax">
        <div className="hero-content">
          {isLoggedIn && <h2 className="greeting-text">Hey, {userName}!</h2>}
          <h1 className="hero-title">PDF Intelligence, Powered by AI</h1>
          <p className="hero-subtitle">
            Upload your documents and interact with them like never before.
          </p>
          <button onClick={handleLaunchClick} className="cta-button">
            Launch PDF Chat App
          </button>
        </div>
      </header>

      {/* --- NEW: Key Features Section --- */}
      <section className="features-section">
        <h2 className="section-title">Core Features</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon"><ChatIcon /></div>
            <h3 className="feature-title">AI-Powered Chat</h3>
            <p className="feature-description">Ask complex questions and get instant, context-aware answers from your documents.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><DocumentIcon /></div>
            <h3 className="feature-title">Instant Summaries</h3>
            <p className="feature-description">Generate concise summaries of lengthy reports in seconds, saving you valuable time.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><ConnectIcon /></div>
            <h3 className="feature-title">Connect the Dots</h3>
            <p className="feature-description">Instantly find related sections and new insights across your entire document library.</p>
          </div>
        </div>
      </section>

      <section className="about-project-section">
        <div className="about-section-container">
          <div className="about-text">
            <h2 className="section-title">About the Project</h2>
            <p className="section-text" style={{ textAlign: 'left' }}>
              This application is a powerful tool designed to revolutionize the way you interact with your PDF documents. By leveraging the capabilities of modern Large Language Models (LLMs), we provide a seamless conversational interface that allows you to "talk" to your files. You can ask complex questions, request summaries of lengthy reports, extract key information, and get insights in seconds, all without manually scrolling through pages.
            </p>
          </div>
          <div className="about-image">
            <img src="https://colorlib.com/wp/wp-content/uploads/sites/2/photo-1443527216320-7e744084f5a7-1.jpg" alt="AI Technology" style={{ width: '100%', borderRadius: '12px' }} />
          </div>
        </div>
      </section>

      <Footer onNavigate={onNavigate} />
    </div>
  );
};

export default HomePage;
