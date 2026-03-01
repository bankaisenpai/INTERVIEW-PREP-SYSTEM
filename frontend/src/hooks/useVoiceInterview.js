// useVoiceInterview.js
// ADD THIS FILE to: frontend/src/hooks/useVoiceInterview.js

import { useState, useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useVoiceInterview() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [interviewerText, setInterviewerText] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [metrics, setMetrics] = useState({ fillerCount: 0, wpm: 0 });
  const [error, setError] = useState(null);
  
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  // Initialize Speech Recognition
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError('Speech recognition not supported');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript + ' ';
        } else {
          interim += transcript;
        }
      }

      if (final) {
        setTranscript(prev => prev + final);
      }
      setInterimTranscript(interim);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setError(`Recognition error: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  // Start Interview
  const startInterview = async (role, level, mode) => {
    try {
      const response = await fetch(`${API_BASE}/api/interview/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, level, mode })
      });

      if (!response.ok) {
        throw new Error(`Failed to start: ${response.status}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setInterviewerText(data.interviewer_text);
      
      // Speak first question
      speak(data.interviewer_text);
      
      return data;
    } catch (err) {
      setError(err.message);
      console.error('Start interview error:', err);
    }
  };

  // Submit Answer
  const submitAnswer = async () => {
    if (!sessionId || !transcript) return;

    try {
      const response = await fetch(`${API_BASE}/api/interview/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          user_transcript: transcript
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to respond: ${response.status}`);
      }

      const data = await response.json();
      
      setMetrics({
        fillerCount: data.metrics?.filler_count || 0,
        wpm: data.metrics?.wpm || 0
      });
      
      setInterviewerText(data.interviewer_text);
      speak(data.interviewer_text);
      
      // Clear transcript for next answer
      setTranscript('');
      
      return data;
    } catch (err) {
      setError(err.message);
      console.error('Submit answer error:', err);
    }
  };

  // Text-to-Speech
  const speak = (text) => {
    if (synthRef.current.speaking) {
      synthRef.current.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    synthRef.current.speak(utterance);
  };

  // Start/Stop Listening
  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
        setIsListening(true);
        setError(null);
      } catch (err) {
        console.error('Start recognition error:', err);
      }
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const stopSpeaking = () => {
    if (synthRef.current.speaking) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  return {
    // State
    isListening,
    transcript,
    interimTranscript,
    interviewerText,
    isSpeaking,
    sessionId,
    metrics,
    error,
    
    // Actions
    startInterview,
    submitAnswer,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    
    // Utils
    clearTranscript: () => setTranscript(''),
    clearError: () => setError(null)
  };
}