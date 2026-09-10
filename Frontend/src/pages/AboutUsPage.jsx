import React from 'react';
import Footer from '../components/common/Footer';

const AboutUsPage = ({ onNavigate }) => {
    return (
        <div className="page-container">
            {/* --- Hero Banner --- */}
            <header className="about-hero">
                <div className="hero-content">
                    <h1 className="hero-title">The Story Behind the Intelligence</h1>
                    <p className="hero-subtitle">From a complex challenge to a seamless user experience.</p>
                </div>
            </header>

            {/* --- Two-Column Mission Section --- */}
            <section className="about-mission-section">
                <div className="about-section-container">
                    <div className="about-text">
                        <h2 className="section-title">Our Mission</h2>
                        <p className="section-text" style={{ textAlign: 'left' }}>
                            Our mission is to bridge the gap between static documents and dynamic, intelligent interaction. This project was born from the idea that your documents hold valuable data, and accessing it should be as simple as having a conversation. We are a team of developers and AI enthusiasts passionate about building tools that make information more powerful and intuitive for everyone.
                        </p>
                    </div>
                    <div className="about-image">
                        <img src="https://colorlib.com/wp/wp-content/uploads/sites/2/photo-1443527216320-7e744084f5a7-1.jpg" alt="Artificial Intelligence Concept" style={{ width: '100%', borderRadius: '12px' }} />
                    </div>
                </div>
            </section>

            <Footer onNavigate={onNavigate} />
        </div>
    );
};

export default AboutUsPage;