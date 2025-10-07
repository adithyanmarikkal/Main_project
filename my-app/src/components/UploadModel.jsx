import React, { useState } from 'react';

import { useNavigate, useLocation } from 'react-router-dom';
import './UploadModel.css';

function UploadModel() {
  const navigate = useNavigate();
   const location = useLocation();
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleLogout = () => {
    navigate('/');
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleBrowseClick = () => {
    document.getElementById('fileInput').click();
  };

  const processSteps = [
    {
      number: 1,
      title: 'Download Global Model',
      description: 'Get the latest model parameters from the dashboard'
    },
    {
      number: 2,
      title: 'Train Locally',
      description: 'Train on your private data without sharing it'
    },
    {
      number: 3,
      title: 'Share Updates Only',
      description: 'Upload only model weights, not raw data'
    },
    {
      number: 4,
      title: 'Secure on Blockchain',
      description: 'Your contribution is recorded immutably'
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
            My Contributions
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
          <h1 className="page-title">Upload Model</h1>
          <p className="page-description">
            Upload your locally trained model updates to contribute to the global federated learning network.
          </p>
        </div>

        <section className="process-card">
          <div className="process-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L4 6v6c0 5.5 3.8 10.7 8 12 4.2-1.3 8-6.5 8-12V6l-8-4z" fill="#3B82F6"/>
            </svg>
            <h2>Federated Learning Process</h2>
          </div>
          <p className="process-description">Follow these steps to securely contribute your model updates</p>

          <div className="steps-grid">
            {processSteps.map((step) => (
              <div key={step.number} className="step-card">
                <div className="step-number">{step.number}</div>
                <h3 className="step-title">{step.title}</h3>
                <p className="step-description">{step.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="upload-card">
          <h2 className="upload-title">Upload Your Model Update</h2>
          <p className="upload-description">Select your trained model file to contribute to the network</p>

          <div 
            className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input 
              type="file" 
              id="fileInput"
              className="file-input"
              onChange={handleFileChange}
              accept=".h5,.pkl,.pt,.pth,.model"
            />
            
            <div className="upload-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>

            {selectedFile ? (
              <div className="file-selected">
                <p className="file-name">{selectedFile.name}</p>
                <p className="file-size">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            ) : (
              <>
                <p className="upload-text">Drop your model file here</p>
                <p className="upload-subtext">Or click to browse your files</p>
              </>
            )}

            <button className="browse-btn" onClick={handleBrowseClick}>
              Browse Files
            </button>

            <p className="supported-formats">
              Supported formats: .h5, .pkl, .pt, .pth, .model (Max 100MB)
            </p>
          </div>

          {selectedFile && (
            <button className="submit-btn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              Upload Model
            </button>
          )}
        </section>
      </main>
    </div>
  );
}

export default UploadModel;