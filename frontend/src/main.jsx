// main.jsx - FIXED VERSION (No /voice route duplication)
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Scene3D from './Scene3D';
import './index.css';

/**
 * IMPORTANT: Only ONE route - the 3D scene embedded in Streamlit
 * 
 * The /voice route has been REMOVED to prevent duplication.
 * Voice interview is handled by the FastAPI backend (api_extensions.py)
 * NOT as a separate React page.
 * 
 * Streamlit shows the interview UI with text input.
 * React only shows the 3D avatar that animates based on talking state.
 */

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Main route - 3D Avatar Scene (embedded in Streamlit iframe) */}
        <Route path="/" element={<Scene3D />} />
        
        {/* NO /voice route - removed to prevent duplication */}
        {/* Voice interview is handled by Streamlit + FastAPI backend */}
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);