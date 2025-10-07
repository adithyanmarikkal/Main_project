// Login.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';

function Login() {
  const [account, setAccount] = useState(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const connectMetaMask = async () => {
    if (typeof window.ethereum !== 'undefined') {
      try {
        const accounts = await window.ethereum.request({ 
          method: 'eth_requestAccounts' 
        });
        setAccount(accounts[0]);
        setError('');
        
        // Navigate to dashboard after successful login
        setTimeout(() => {
          navigate('/dashboard');
        }, 1000);
      } catch (err) {
        setError('Failed to connect to MetaMask');
        console.error(err);
      }
    } else {
      setError('MetaMask is not installed. Please install it to continue.');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="logo-section">
          <div className="shield-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L4 6v6c0 5.5 3.8 10.7 8 12 4.2-1.3 8-6.5 8-12V6l-8-4z" fill="#3B82F6"/>
            </svg>
          </div>
          <h1 className="brand-name">FedShield</h1>
        </div>

        <h2 className="welcome-text">Welcome Back</h2>
        <p className="subtitle">Sign in to access the secure network</p>

        {account ? (
          <div className="success-section">
            <p className="success-text">Connected Successfully!</p>
            <p className="account-text">{account.slice(0, 6)}...{account.slice(-4)}</p>
            <p className="redirect-text">Redirecting to dashboard...</p>
          </div>
        ) : (
          <button className="metamask-button" onClick={connectMetaMask}>
            Login with MetaMask
          </button>
        )}

        {error && <p className="error-text">{error}</p>}
      </div>
    </div>
  );
}

export default Login;

