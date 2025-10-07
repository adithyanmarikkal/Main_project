import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import UploadModel from './components/UploadModel';
import Contributions from './components/Contributions'; 
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<UploadModel />} />
        <Route path="/contributions" element={<Contributions />} />
      </Routes>
    </Router>
  );
}

export default App;