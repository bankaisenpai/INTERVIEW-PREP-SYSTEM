import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Scene3D from './Scene3D'  // Your 3D avatar code
import LiveInterviewPanel from './components/LiveInterviewPanel'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
    <BrowserRouter>
      <Routes>
        {/* 3D Scene route */}
        <Route path="/" element={<Scene3D />} />
        
        {/* Voice Interview route */}
        <Route path="/voice" element={
          <LiveInterviewPanel 
            role="Data Scientist" 
            level="Intermediate" 
            mode="practice" 
          />
        } />
      </Routes>
    </BrowserRouter>
)