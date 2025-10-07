import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Dashboard.css';

function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const handleLogout = () => {
    navigate('/');
  };

  const modelHistory = [
    {
      version: 'v4.2',
      current: true,
      accuracy: '98.89%',
      change: '+0.12%',
      blockchainTx: '0x7a4f...8c3d',
      date: '2024-01-15'
    },
    {
      version: 'v4.1',
      current: false,
      accuracy: '98.77%',
      change: '+0.08%',
      blockchainTx: '0x5b2e...7f9a',
      date: '2024-01-10'
    },
    {
      version: 'v4.0',
      current: false,
      accuracy: '98.69%',
      change: '+0.15%',
      blockchainTx: '0x3c1a...6e2b',
      date: '2024-01-05'
    },
    {
      version: 'v3.9',
      current: false,
      accuracy: '98.54%',
      change: '+0.09%',
      blockchainTx: '0x9d8f...4a1c',
      date: '2024-01-01'
    }
  ];

  return (
    <div className="dashboard-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L4 6v6c0 5.5 3.8 10.7 8 12 4.2-1.3 8-6.5 8-12V6l-8-4z" fill="#3B82F6"/>
            </svg>
          </div>
          <h2 className="sidebar-brand">FedShield</h2>
        </div>

        <nav className="sidebar-nav">
<button 
      className={`nav-item ${location.pathname === '/dashboard' ? 'active' : ''}`}
      onClick={() => navigate('/dashboard')}
    >

            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            Dashboard
          </button>
          <button 
      className={`nav-item ${location.pathname === '/upload' ? 'active' : ''}`}
      onClick={() => navigate('/upload')}
    >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Upload Model
          </button>
         <button 
      className={`nav-item ${location.pathname === '/contributions' ? 'active' : ''}`}
      onClick={() => navigate('/contributions')}
    >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7"/>
              <rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/>
            </svg>
            Contributions
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div className="user-details">
              <p className="user-name">John Researcher</p>
              <p className="user-email">john@university.edu</p>
            </div>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Logout
          </button>
        </div>
      </aside>

      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">Dashboard</h1>
          <p className="page-description">
            Welcome to FedShield's collaborative intrusion detection network. Download the latest global
            model, train it with your local data, and contribute to improving IoT security for everyone.
          </p>
        </div>

        <section className="model-card">
          <div className="model-header">
            <div className="model-title-section">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L4 6v6c0 5.5 3.8 10.7 8 12 4.2-1.3 8-6.5 8-12V6l-8-4z" fill="#3B82F6"/>
              </svg>
              <h2>Current Global Model</h2>
            </div>
            <span className="version-badge">Version v4.2</span>
          </div>
          <p className="model-description">
            Latest federated learning model trained on CICIDS-2018 and CICIOT-2023 datasets
          </p>

          <div className="model-stats">
            <div className="stat-item">
              <div className="stat-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              </div>
              <div className="stat-details">
                <p className="stat-label">Global Accuracy</p>
                <p className="stat-value accuracy">98.89%</p>
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
              </div>
              <div className="stat-details">
                <p className="stat-label">Last Aggregation</p>
                <p className="stat-value">Jan 15, 2024</p>
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                </svg>
              </div>
              <div className="stat-details">
                <p className="stat-label">Training Data</p>
                <p className="stat-value">CICIDS-2018, CICIOT-2023</p>
              </div>
            </div>
          </div>

          <button className="download-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Download Model Parameters
          </button>
        </section>

        <section className="history-section">
          <h2 className="section-title">Global Model History</h2>
          <p className="section-description">Complete timeline of model versions with blockchain verification</p>

          <div className="timeline">
            {modelHistory.map((model, index) => (
              <div key={index} className="timeline-item">
                <div className="timeline-marker">
                  <div className={`marker-dot ${model.current ? 'current' : ''}`}></div>
                  {index < modelHistory.length - 1 && <div className="timeline-line"></div>}
                </div>
                <div className="timeline-content">
                  <div className="timeline-header">
                    <div className="version-info">
                      <h3 className="version-number">{model.version}</h3>
                      {model.current && <span className="current-badge">Current</span>}
                    </div>
                    <span className="timeline-date">{model.date}</span>
                  </div>
                  <div className="timeline-details">
                    <span className="detail-item">
                      Accuracy: <strong>{model.accuracy}</strong> 
                      <span className="accuracy-change">{model.change}</span>
                    </span>
                    <span className="detail-item">
                      # Blockchain TX: <code>{model.blockchainTx}</code>
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default Dashboard;