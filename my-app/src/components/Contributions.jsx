// Contributions.jsx
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Dashboard.css'; // For sidebar styles
import './Contributions.css'; // For contributions-specific styles

function Contributions() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    navigate('/');
  };

  const contributionHistory = [
    {
      date: '2024-01-15',
      fileName: 'model_update_v4.2.h5',
      status: 'Included',
      statusDetail: 'Included in Global Model v4.2',
      accuracyImpact: '+0.12%',
      blockchainTx: '0x7a4f...8c3d'
    },
    {
      date: '2024-01-12',
      fileName: 'federated_weights_v4.1.pkl',
      status: 'Included',
      statusDetail: 'Included in Global Model v4.1',
      accuracyImpact: '+0.08%',
      blockchainTx: '0x5b2e...7f9a'
    },
    {
      date: '2024-01-08',
      fileName: 'local_model_update.pt',
      status: 'Included',
      statusDetail: 'Included in Global Model v4.0',
      accuracyImpact: '+0.15%',
      blockchainTx: '0x3c1a...6e2b'
    },
    {
      date: '2024-01-05',
      fileName: 'training_update_v4.3.h5',
      status: 'Pending',
      statusDetail: 'Pending Aggregation',
      accuracyImpact: 'Pending',
      blockchainTx: '#'
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
          <h1 className="page-title">My Contributions</h1>
          <p className="page-description">
            Track all your model contributions to the FedShield network with blockchain verification.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="contributions-stats">
          <div className="stat-card">
            <h3 className="stat-number">4</h3>
            <p className="stat-description">Total Contributions</p>
          </div>
          <div className="stat-card">
            <h3 className="stat-number">3</h3>
            <p className="stat-description">Included in Models</p>
          </div>
          <div className="stat-card">
            <h3 className="stat-number">1</h3>
            <p className="stat-description">Pending Review</p>
          </div>
          <div className="stat-card">
            <h3 className="stat-number">+0.12%</h3>
            <p className="stat-description">Avg. Accuracy Boost</p>
          </div>
        </div>

        {/* Contribution History Table */}
        <section className="history-section">
          <div className="section-header">
            <div>
              <h2 className="section-title">Contribution History</h2>
              <p className="section-description">Detailed log of all your model uploads with blockchain verification</p>
            </div>
          </div>

          <div className="contribution-table">
            <table>
              <thead>
                <tr>
                  <th>Submission Date</th>
                  <th>File Name</th>
                  <th>Status</th>
                  <th>Accuracy Impact</th>
                  <th>Blockchain TX</th>
                </tr>
              </thead>
              <tbody>
                {contributionHistory.map((contribution, index) => (
                  <tr key={index}>
                    <td>
                      <div className="date-cell">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2">
                          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                          <line x1="16" y1="2" x2="16" y2="6"/>
                          <line x1="8" y1="2" x2="8" y2="6"/>
                          <line x1="3" y1="10" x2="21" y2="10"/>
                        </svg>
                        {contribution.date}
                      </div>
                    </td>
                    <td>
                      <div className="file-cell">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2">
                          <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
                          <polyline points="13 2 13 9 20 9"/>
                        </svg>
                        {contribution.fileName}
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge ${contribution.status.toLowerCase()}`}>
                        {contribution.status}
                      </span>
                      <div className="status-detail">{contribution.statusDetail}</div>
                    </td>
                    <td>
                      <span className={contribution.status === 'Included' ? 'accuracy-positive' : 'accuracy-pending'}>
                        {contribution.accuracyImpact}
                      </span>
                    </td>
                    <td>
                      <code className="blockchain-hash">{contribution.blockchainTx}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Blockchain Verification Info */}
        <section className="info-card">
          <div className="info-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div className="info-content">
            <h3 className="info-title">Blockchain Verification</h3>
            <p className="info-description">
              Every contribution is recorded on the blockchain, providing immutable proof of your 
              participation in the federated learning network. Transaction IDs can be verified on the 
              blockchain explorer.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default Contributions;