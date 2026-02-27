import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './Pages/login'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default route → go to login */}
        <Route path="/" element={<Navigate to="/login" />} />

        {/* Login page */}
        <Route path="/login" element={<Login />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App