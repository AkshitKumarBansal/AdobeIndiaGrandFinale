import React from 'react';
import { GithubIcon, LinkedinIcon, TwitterIcon } from './Icons';

const Footer = ({ onNavigate }) => {
    const handleNavClick = (page) => {
        onNavigate(page);
        window.scrollTo(0, 0); // This line scrolls the window to the top
    };

    return (
        <footer className="footer-enhanced">
            <div className="footer-content">
                <div className="footer-section footer-about">
                    <h3 className="footer-title">PaperTrail</h3>
                    <p>Revolutionizing the way you interact with your documents. Ask questions, get summaries, and connect insights like never before.</p>
                </div>
                <div className="footer-section footer-links">
                    <h3 className="footer-title">Quick Links</h3>
                    <ul>
                        <li><a href="#home" onClick={() => handleNavClick("home")} className="footer-link">Home</a></li>
                        <li><a href="#about" onClick={() => handleNavClick("about")} className="footer-link">About Us</a></li>
                        <li><a href="#contact" onClick={() => handleNavClick("contact")} className="footer-link">Contact Us</a></li>
                    </ul>
                </div>
                <div className="footer-section footer-social">
                    <h3 className="footer-title">Follow Us</h3>
                    <div className="social-icons">
                        <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="social-icon-link">
                            <GithubIcon />
                        </a>
                        <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="social-icon-link">
                            <LinkedinIcon />
                        </a>
                        <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="social-icon-link">
                            <TwitterIcon />
                        </a>
                    </div>
                </div>
            </div>
            <div className="footer-bottom">
                &copy; {new Date().getFullYear()} PaperTrail | All Rights Reserved
            </div>
        </footer>
    );
};

export default Footer;