// LiveInterviewPanel.jsx
// ADD THIS FILE to: frontend/src/components/LiveInterviewPanel.jsx
// Then import and use in your Streamlit page or as a new route

import React, { useState, useEffect } from 'react';
import { useVoiceInterview } from '../hooks/useVoiceInterview';

export function LiveInterviewPanel({ role = "Data Scientist", level = "Intermediate", mode = "practice" }) {
  const {
    isListening,
    transcript,
    interimTranscript,
    interviewerText,
    isSpeaking,
    metrics,
    error,
    startInterview,
    submitAnswer,
    startListening,
    stopListening,
    speak,
    stopSpeaking
  } = useVoiceInterview();

  const [interviewStarted, setInterviewStarted] = useState(false);
  const [conversationLog, setConversationLog] = useState([]);
  const [timer, setTimer] = useState(0);

  // Timer
  useEffect(() => {
    if (!interviewStarted) return;
    
    const interval = setInterval(() => {
      setTimer(prev => prev + 1);
    }, 1000);
    
    return () => clearInterval(interval);
  }, [interviewStarted]);

  const handleStart = async () => {
    const result = await startInterview(role, level, mode);
    if (result) {
      setInterviewStarted(true);
      setConversationLog([{ role: 'interviewer', text: result.interviewer_text }]);
    }
  };

  const handleSubmit = async () => {
    if (!transcript) return;
    
    stopListening();
    
    // Add user answer to log
    setConversationLog(prev => [...prev, { role: 'user', text: transcript }]);
    
    const result = await submitAnswer();
    if (result) {
      setConversationLog(prev => [...prev, { role: 'interviewer', text: result.interviewer_text }]);
      
      if (result.complete) {
        setInterviewStarted(false);
      }
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={styles.container}>
      {/* Top Bar */}
      <div style={styles.topBar}>
        <div style={styles.status}>
          <span style={{
            ...styles.statusDot,
            background: interviewStarted ? (isListening ? '#ef4444' : isSpeaking ? '#10b981' : '#6b7280') : '#6b7280'
          }} />
          <span style={styles.statusText}>
            {!interviewStarted ? 'Not Started' : isListening ? 'Listening...' : isSpeaking ? 'AI Speaking' : 'Ready'}
          </span>
        </div>
         <a 
    href="/" 
    style={{
      color: 'white',
      textDecoration: 'none',
      padding: '8px 16px',
      background: 'rgba(255,255,255,0.1)',
      borderRadius: '8px'
    }}
  >
    ← Back to 3D Scene
  </a>
        
        <div style={styles.timer}>
          ⏱️ {formatTime(timer)}
        </div>
        
        <div style={styles.mode}>
          {mode === 'practice' ? '🎓 Practice Mode' : '🎯 Real Interview'}
        </div>
      </div>

      {/* Main Content */}
      <div style={styles.content}>
        
        {/* Captions Box */}
        <div style={styles.captionsBox}>
          <div style={styles.captionLabel}>Live Transcript</div>
          
          {interviewerText && (
            <div style={styles.interviewerCaption}>
              <strong>🎤 Interviewer:</strong> {interviewerText}
            </div>
          )}
          
          {(transcript || interimTranscript) && (
            <div style={styles.userCaption}>
              <strong>👤 You:</strong> {transcript}
              {interimTranscript && <span style={styles.interim}>{interimTranscript}</span>}
            </div>
          )}
          
          {!interviewerText && !transcript && (
            <div style={styles.placeholder}>
              {interviewStarted ? 'Waiting for response...' : 'Click START to begin interview'}
            </div>
          )}
        </div>

        {/* Controls */}
        <div style={styles.controls}>
          {!interviewStarted ? (
            <button onClick={handleStart} style={styles.primaryButton}>
              🚀 START INTERVIEW
            </button>
          ) : (
            <>
              {!isListening ? (
                <button onClick={startListening} style={styles.primaryButton}>
                  🎤 Start Speaking
                </button>
              ) : (
                <button onClick={stopListening} style={{...styles.primaryButton, background: '#ef4444'}}>
                  ⏹️ Stop
                </button>
              )}
              
              <button 
                onClick={handleSubmit} 
                style={styles.secondaryButton}
                disabled={!transcript}
              >
                📤 Submit Answer
              </button>
              
              {isSpeaking && (
                <button onClick={stopSpeaking} style={styles.secondaryButton}>
                  🔇 Stop AI
                </button>
              )}
            </>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div style={styles.error}>
            ⚠️ {error}
          </div>
        )}

        {/* Conversation Log */}
        <div style={styles.logContainer}>
          <div style={styles.logTitle}>Conversation History</div>
          <div style={styles.log}>
            {conversationLog.map((entry, idx) => (
              <div 
                key={idx} 
                style={{
                  ...styles.logEntry,
                  background: entry.role === 'interviewer' ? '#e3f2fd' : '#f3e5f5'
                }}
              >
                <strong>{entry.role === 'interviewer' ? '🎤' : '👤'} {entry.role}:</strong>
                <p>{entry.text}</p>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Right Panel - Metrics */}
      <div style={styles.rightPanel}>
        <h3 style={styles.panelTitle}>Live Feedback</h3>
        
        <div style={styles.metricCard}>
          <div style={styles.metricLabel}>Filler Words</div>
          <div style={styles.metricValue}>{metrics.fillerCount}</div>
          <div style={styles.metricHint}>
            {metrics.fillerCount < 3 ? '✅ Good' : '⚠️ Try to reduce'}
          </div>
        </div>
        
        <div style={styles.metricCard}>
          <div style={styles.metricLabel}>Speaking Rate</div>
          <div style={styles.metricValue}>{metrics.wpm} WPM</div>
          <div style={styles.metricHint}>
            {metrics.wpm > 100 && metrics.wpm < 160 ? '✅ Ideal' : '💡 Adjust pace'}
          </div>
        </div>
        
        <div style={styles.metricCard}>
          <div style={styles.metricLabel}>Confidence</div>
          <div style={styles.metricValue}>
            {metrics.fillerCount < 3 && metrics.wpm > 100 ? 'High' : 'Medium'}
          </div>
        </div>
      </div>
    </div>
  );
}

// Styles
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: '#f5f5f5',
    fontFamily: 'system-ui, sans-serif'
  },
  topBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 24px',
    background: '#1a1a1a',
    color: 'white',
    borderBottom: '2px solid #333'
  },
  status: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  statusDot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    animation: 'pulse 2s infinite'
  },
  statusText: {
    fontWeight: 600
  },
  timer: {
    fontSize: '18px',
    fontWeight: 700
  },
  mode: {
    padding: '6px 12px',
    background: '#667eea',
    borderRadius: '20px',
    fontSize: '14px',
    fontWeight: 600
  },
  content: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    padding: '24px',
    gap: '20px',
    overflow: 'auto'
  },
  captionsBox: {
    background: 'white',
    borderRadius: '12px',
    padding: '20px',
    minHeight: '200px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
  },
  captionLabel: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '12px',
    fontWeight: 600
  },
  interviewerCaption: {
    background: '#e3f2fd',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '12px',
    borderLeft: '4px solid #2196f3'
  },
  userCaption: {
    background: '#f3e5f5',
    padding: '12px',
    borderRadius: '8px',
    borderLeft: '4px solid #9c27b0'
  },
  interim: {
    opacity: 0.6,
    fontStyle: 'italic'
  },
  placeholder: {
    color: '#999',
    textAlign: 'center',
    padding: '40px',
    fontSize: '16px'
  },
  controls: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center'
  },
  primaryButton: {
    padding: '14px 28px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: 600,
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)'
  },
  secondaryButton: {
    padding: '14px 28px',
    background: '#f5f5f5',
    color: '#333',
    border: '2px solid #ddd',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: 600,
    cursor: 'pointer'
  },
  error: {
    background: '#fee',
    color: '#c00',
    padding: '12px',
    borderRadius: '8px',
    textAlign: 'center'
  },
  logContainer: {
    background: 'white',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
  },
  logTitle: {
    fontWeight: 700,
    marginBottom: '12px',
    color: '#333'
  },
  log: {
    maxHeight: '300px',
    overflow: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px'
  },
  logEntry: {
    padding: '12px',
    borderRadius: '8px',
    borderLeft: '4px solid #2196f3'
  },
  rightPanel: {
    position: 'fixed',
    right: 0,
    top: 70,
    width: '280px',
    height: 'calc(100vh - 70px)',
    background: 'white',
    padding: '20px',
    boxShadow: '-2px 0 8px rgba(0,0,0,0.1)',
    overflowY: 'auto'
  },
  panelTitle: {
    margin: '0 0 20px 0',
    color: '#333'
  },
  metricCard: {
    background: '#f9f9f9',
    padding: '16px',
    borderRadius: '8px',
    marginBottom: '16px',
    textAlign: 'center'
  },
  metricLabel: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '8px'
  },
  metricValue: {
    fontSize: '32px',
    fontWeight: 700,
    color: '#333',
    marginBottom: '4px'
  },
  metricHint: {
    fontSize: '12px',
    color: '#999'
  }
};

export default LiveInterviewPanel;