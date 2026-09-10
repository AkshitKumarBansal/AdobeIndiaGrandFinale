import React, { useState } from 'react';
import { CloseIcon } from '../common/Icons';
import apiClient from '../../api/apiClient';

const LoginModal = ({ isOpen, onClose, onLogin }) => {
    const [isSignup, setIsSignup] = useState(false);
    const [error, setError] = useState('');

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        const email = e.target.elements.email.value;
        const password = e.target.elements.password.value;
        const name = e.target.elements.name?.value;

        try {
            if (isSignup) {
                await apiClient.post('/register', { email, password, name });
                const response = await apiClient.post('/login', { email, password });
                onLogin(response.data.user_name, response.data.access_token);
            } else {
                const response = await apiClient.post('/login', { email, password });
                onLogin(response.data.user_name, response.data.access_token);
            }
            onClose();
        } catch (err) {
            setError(err.response?.data?.detail || 'An error occurred.');
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <button className="modal-close-button" onClick={onClose}>
                    <CloseIcon color="var(--text)" />
                </button>
                <h2 className="modal-title">{isSignup ? 'Create Account' : 'Welcome Back'}</h2>
                <form onSubmit={handleSubmit} className="modal-form">
                    {isSignup && <input name="name" type="text" placeholder="Your Name" className="modal-input" required />}
                    <input name="email" type="email" placeholder="Email Address" className="modal-input" required />
                    <input name="password" type="password" placeholder="Password" className="modal-input" required />
                    {error && <p className="error-message">{error}</p>}
                    <button type="submit" className="modal-submit-button">
                        {isSignup ? 'Sign Up' : 'Login'}
                    </button>
                </form>
                <p className="modal-toggle-text">
                    {isSignup ? 'Already have an account?' : "Don't have an account?"}
                    <span onClick={() => setIsSignup(!isSignup)} className="modal-toggle-link">
                        {isSignup ? ' Login' : ' Sign Up'}
                    </span>
                </p>
            </div>
        </div>
    );
};

export default LoginModal;