import React, { useState, useEffect, useRef } from "react";
import ReactDOM from "react-dom/client";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF, useAnimations } from "@react-three/drei";
import * as THREE from "three";

// ═══════════════════════════════════════════════════════════
// SPEECH RECOGNITION HOOK
// ═══════════════════════════════════════════════════════════
function useSpeechRecognition() {
  const [transcript, setTranscript] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setIsSupported(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      setTranscript(prev => prev + finalTranscript || interimTranscript);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
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

  const startListening = () => {
    if (recognitionRef.current && !isListening && isSupported) {
      setTranscript("");
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (error) {
        console.error('Error starting recognition:', error);
      }
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const clearTranscript = () => {
    setTranscript("");
  };

  return { transcript, isListening, isSupported, startListening, stopListening, clearTranscript };
}

// ═══════════════════════════════════════════════════════════
// AVATAR COMPONENT - WITH PROPER ANIMATION SYNC
// ═══════════════════════════════════════════════════════════
function Avatar({ isTalking, position = [0, 0.10, -0.0] }) {
  const group = useRef();
  const { scene } = useGLTF("/character.glb");
  const sitting = useGLTF("/animations/Sitting.glb");
  const talking = useGLTF("/animations/Talking.glb");

  const animations = [...sitting.animations, ...talking.animations];
  const { actions } = useAnimations(animations, group);

  // Character scaling
  useEffect(() => {
    if (!scene) return;
    const box = new THREE.Box3().setFromObject(scene);
    const size = box.getSize(new THREE.Vector3());
    const targetHeight = 3;
    let scale = targetHeight / size.y;
    scale = Math.min(scale, 1.3);
    scale = Math.max(scale, 0.2);
    scene.scale.set(scale, scale, scale);
    const newBox = new THREE.Box3().setFromObject(scene);
    const newCenter = newBox.getCenter(new THREE.Vector3());
    scene.position.set(-newCenter.x, -newBox.min.y, -newCenter.z - 0.03);
  }, [scene]);

  // Animation control - ONLY PLAY TALKING WHEN isTalking is TRUE
  useEffect(() => {
    if (!actions || !sitting.animations[0]) return;

    // Stop all animations first
    Object.values(actions).forEach((action) => {
      if (action) action.stop();
    });

    if (isTalking && talking.animations[0]) {
      // Avatar is speaking - play talking animation
      const talkAction = actions[talking.animations[0].name];
      if (talkAction) {
        talkAction.reset().setLoop(THREE.LoopRepeat, Infinity).play();
        console.log("🗣️ Talking animation started");
      }
    } else if (sitting.animations[0]) {
      // Avatar is idle - play sitting animation
      const sitAction = actions[sitting.animations[0].name];
      if (sitAction) {
        sitAction.reset().setLoop(THREE.LoopRepeat, Infinity).play();
        console.log("💺 Sitting animation started");
      }
    }
  }, [isTalking, actions, sitting, talking]);

  return <primitive ref={group} object={scene} position={position} castShadow />;
}

// ═══════════════════════════════════════════════════════════
// INTERVIEW SCENE
// ═══════════════════════════════════════════════════════════
function InterviewScene({ isTalking }) {
  return (
    <>
      <color attach="background" args={["#1a1f35"]} />
      <fog attach="fog" args={["#1a1f35", 5, 20]} />
      <OrbitControls
        target={[0, 1, 0]}
        enableDamping
        dampingFactor={0.06}
        minDistance={4.2}
        maxDistance={4.8}
        minPolarAngle={Math.PI / 4}
        maxPolarAngle={Math.PI / 2.2}
        maxAzimuthAngle={Math.PI / 6}
        minAzimuthAngle={-Math.PI / 6}
        enablePan={false}
      />
      <ambientLight intensity={0.35} />
      <directionalLight
        position={[4, 8, 5]}
        intensity={1}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      <directionalLight position={[-4, 4, -3]} intensity={0.5} color="#9bb5ff" />
      <directionalLight position={[0, 5, -8]} intensity={0.7} />
      <spotLight position={[0, 3.5, 4]} angle={0.5} penumbra={0.5} intensity={0.4} color="#fff8f0" />
      
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[15, 15]} />
        <meshStandardMaterial color="#2d3748" roughness={0.85} />
      </mesh>
      <gridHelper args={[12, 24, "#3d4a5c", "#2a3441"]} position={[0, 0.005, 0]} />
      
      <mesh position={[0, 0.76, 0.5]} castShadow receiveShadow>
        <boxGeometry args={[2.0, 0.06, 0.9]} />
        <meshStandardMaterial color="#4a3728" roughness={0.6} />
      </mesh>
      
      {[[-0.9, 0.38, 0.8], [0.9, 0.38, 0.8], [-0.9, 0.38, 0.2], [0.9, 0.38, 0.2]].map((pos, i) => (
        <mesh key={i} position={pos} castShadow>
          <cylinderGeometry args={[0.03, 0.03, 0.76, 12]} />
          <meshStandardMaterial color="#2c3e50" roughness={0.4} metalness={0.7} />
        </mesh>
      ))}
      
      <mesh position={[0.15, 0.80, 0.45]} castShadow>
        <boxGeometry args={[0.4, 0.02, 0.28]} />
        <meshStandardMaterial color="#1e293b" metalness={0.6} />
      </mesh>
      
      <mesh position={[0.15, 0.96, 0.32]} rotation={[-0.25, 0, 0]} castShadow>
        <boxGeometry args={[0.4, 0.3, 0.015]} />
        <meshStandardMaterial color="#1e293b" metalness={0.6} />
      </mesh>
      
      <mesh position={[0.15, 0.96, 0.315]} rotation={[-0.25, 0, 0]}>
        <planeGeometry args={[0.36, 0.26]} />
        <meshBasicMaterial color="#3b82f6" />
      </mesh>
      
      <mesh position={[0, 0.52, -0.15]} castShadow receiveShadow>
        <boxGeometry args={[0.8, 0.08, 0.7]} />
        <meshStandardMaterial color="#2d3748" roughness={0.5} metalness={0.4} />
      </mesh>
      
      <mesh position={[0, 0.95, -0.45]} castShadow>
        <boxGeometry args={[0.8, 0.9, 0.08]} />
        <meshStandardMaterial color="#2d3748" roughness={0.5} metalness={0.4} />
      </mesh>
      
      <mesh position={[0, 0.1, -0.1]}>
        <cylinderGeometry args={[0.25, 0.25, 0.03, 5]} />
        <meshStandardMaterial color="#2c3e50" roughness={0.4} metalness={0.7} />
      </mesh>
      
      <mesh position={[0, 2.5, -4]} receiveShadow>
        <planeGeometry args={[12, 5]} />
        <meshStandardMaterial color="#1e293b" roughness={0.9} />
      </mesh>
      
      <mesh position={[-6, 2.5, 0]} rotation={[0, Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[8, 5]} />
        <meshStandardMaterial color="#141b2d" roughness={0.9} />
      </mesh>
      
      <mesh position={[6, 2.5, 0]} rotation={[0, -Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[8, 5]} />
        <meshStandardMaterial color="#141b2d" roughness={0.9} />
      </mesh>
      
      <mesh position={[-1.5, 0.125, -1.2]}>
        <cylinderGeometry args={[0.12, 0.15, 0.25, 16]} />
        <meshStandardMaterial color="#4a3728" />
      </mesh>
      
      {[...Array(5)].map((_, i) => (
        <mesh key={i} position={[-1.5 + Math.cos(i) * 0.08, 0.28 + i * 0.08, -1.2 + Math.sin(i) * 0.08]}>
          <sphereGeometry args={[0.1, 8, 8]} />
          <meshStandardMaterial color="#2d5016" roughness={0.8} />
        </mesh>
      ))}
      
      <mesh position={[2.2, 0.75, -1.5]} castShadow>
        <boxGeometry args={[0.4, 1.5, 0.3]} />
        <meshStandardMaterial color="#3d2b1f" />
      </mesh>
      
      {[...Array(8)].map((_, i) => {
        const colors = ["#7f1d1d", "#1e3a8a", "#065f46", "#78350f"];
        return (
          <mesh key={i} position={[2.2 - 0.15 + (i % 4) * 0.07, 0.3 + Math.floor(i / 4) * 0.35, -1.5]}>
            <boxGeometry args={[0.06, 0.15, 0.2]} />
            <meshStandardMaterial color={colors[i % colors.length]} />
          </mesh>
        );
      })}
      
      <Avatar isTalking={isTalking} />
    </>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════════
function App() {
  const [isTalking, setIsTalking] = useState(false);
  const [jobRole, setJobRole] = useState("Data Scientist");
  const [difficulty, setDifficulty] = useState("Intermediate");
  const [showVoicePanel, setShowVoicePanel] = useState(false);
  
  const { transcript, isListening, isSupported, startListening, stopListening, clearTranscript } = useSpeechRecognition();

  // TTS function with proper talking state management
  const speak = (text) => {
    // Cancel any ongoing speech
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    
    utterance.onstart = () => {
      console.log("🗣️ Speech started");
      setIsTalking(true);
    };
    
    utterance.onend = () => {
      console.log("🔇 Speech ended");
      setIsTalking(false);
    };
    
    utterance.onerror = (event) => {
      console.error("Speech error:", event);
      setIsTalking(false);
    };
    
    window.speechSynthesis.speak(utterance);
  };

  const sampleQuestions = [
    "Hello! Welcome to your AI interview. Can you tell me about your experience with machine learning?",
    "What is the difference between supervised and unsupervised learning?",
    "Explain what overfitting means and how you would prevent it.",
    "Can you describe a machine learning project you've worked on?",
    "What programming languages are you most comfortable with?",
    "How do you handle imbalanced datasets in machine learning?"
  ];

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative", overflow: "hidden", fontFamily: "Inter, system-ui, sans-serif" }}>
      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [0, 1.3, 4.5], fov: 45 }}
        gl={{
          antialias: true,
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1,
          outputColorSpace: THREE.SRGBColorSpace
        }}
      >
        <InterviewScene isTalking={isTalking} />
      </Canvas>

      <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
        
        {/* Top Bar */}
        <div style={{ 
          position: "absolute", 
          top: 0, 
          left: 0, 
          right: 0, 
          height: "70px", 
          background: "rgba(0,0,0,0.9)", 
          backdropFilter: "blur(20px)", 
          display: "flex", 
          alignItems: "center", 
          justifyContent: "space-between", 
          padding: "0 30px",
          borderBottom: "1px solid rgba(255,255,255,0.1)",
          pointerEvents: "auto",
          boxShadow: "0 4px 12px rgba(0,0,0,0.3)"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
            <div style={{ 
              width: "50px", 
              height: "50px", 
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", 
              borderRadius: "14px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "26px",
              boxShadow: "0 4px 12px rgba(102, 126, 234, 0.4)"
            }}>
              🎤
            </div>
            <div>
              <h1 style={{ color: "white", fontSize: "24px", fontWeight: "700", margin: 0 }}>AI Interview Prep</h1>
              <p style={{ color: "#9ca3af", fontSize: "13px", margin: 0 }}>Practice with Real-time Feedback</p>
            </div>
          </div>
          
          <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: "10px", 
              background: "rgba(255,255,255,0.08)", 
              padding: "10px 18px", 
              borderRadius: "25px",
              border: "1px solid rgba(255,255,255,0.1)"
            }}>
              <div style={{ 
                width: "14px", 
                height: "14px", 
                borderRadius: "50%", 
                backgroundColor: isTalking ? "#10b981" : isListening ? "#ef4444" : "#6b7280",
                boxShadow: (isTalking || isListening) ? "0 0 10px currentColor" : "none",
                animation: (isTalking || isListening) ? "pulse 1.5s infinite" : "none"
              }} />
              <span style={{ color: "white", fontSize: "15px", fontWeight: "600" }}>
                {isTalking ? "AI Speaking..." : isListening ? "Listening..." : "Ready"}
              </span>
            </div>
          </div>
        </div>

        {/* Right Panel */}
        <div style={{ 
          position: "absolute", 
          top: "90px", 
          right: "20px", 
          width: "340px", 
          maxHeight: "calc(100vh - 120px)",
          overflowY: "auto",
          background: "rgba(0,0,0,0.95)", 
          backdropFilter: "blur(20px)", 
          borderRadius: "18px", 
          padding: "26px", 
          pointerEvents: "auto",
          border: "1px solid rgba(255,255,255,0.15)",
          boxShadow: "0 20px 60px rgba(0,0,0,0.6)"
        }}>
          
          <div style={{ marginBottom: "24px" }}>
            <h3 style={{ color: "#60a5fa", fontSize: "19px", marginBottom: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "10px" }}>
              ⚙️ Interview Settings
            </h3>
            
            <div style={{ marginBottom: "18px" }}>
              <label style={{ color: "#9ca3af", fontSize: "14px", display: "block", marginBottom: "9px", fontWeight: "600" }}>Job Role:</label>
              <select 
                style={{ 
                  width: "100%", 
                  padding: "12px 16px", 
                  borderRadius: "10px", 
                  border: "1px solid #374151", 
                  background: "#1f2937", 
                  color: "white", 
                  fontSize: "15px",
                  cursor: "pointer",
                  fontWeight: "500"
                }} 
                value={jobRole} 
                onChange={(e) => setJobRole(e.target.value)}
              >
                <option>Data Scientist</option>
                <option>ML Engineer</option>
                <option>Software Engineer</option>
              </select>
            </div>

            <div style={{ marginBottom: "18px" }}>
              <label style={{ color: "#9ca3af", fontSize: "14px", display: "block", marginBottom: "9px", fontWeight: "600" }}>Difficulty:</label>
              <select 
                style={{ 
                  width: "100%", 
                  padding: "12px 16px", 
                  borderRadius: "10px", 
                  border: "1px solid #374151", 
                  background: "#1f2937", 
                  color: "white", 
                  fontSize: "15px",
                  cursor: "pointer",
                  fontWeight: "500"
                }} 
                value={difficulty} 
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <option>Beginner</option>
                <option>Intermediate</option>
                <option>Advanced</option>
                <option>FAANG</option>
              </select>
            </div>
          </div>

          <div style={{ height: "1px", background: "rgba(255,255,255,0.15)", margin: "24px 0" }} />

          {/* Sample Questions - Avatar speaks these */}
          <div style={{ marginBottom: "24px" }}>
            <h3 style={{ color: "#60a5fa", fontSize: "19px", marginBottom: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "10px" }}>
              🔊 Practice Questions
            </h3>
            
            <div style={{ display: "grid", gap: "10px" }}>
              {sampleQuestions.slice(0, 4).map((question, idx) => (
                <button 
                  key={idx}
                  style={{ 
                    width: "100%", 
                    padding: "14px", 
                    borderRadius: "10px", 
                    border: "none", 
                    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", 
                    color: "white", 
                    fontSize: "14px", 
                    fontWeight: "600", 
                    cursor: "pointer",
                    transition: "all 0.3s",
                    textAlign: "left",
                    boxShadow: "0 4px 12px rgba(102, 126, 234, 0.3)"
                  }} 
                  onClick={() => speak(question)}
                  onMouseOver={(e) => {
                    e.target.style.transform = "translateY(-2px)";
                    e.target.style.boxShadow = "0 6px 16px rgba(102, 126, 234, 0.5)";
                  }}
                  onMouseOut={(e) => {
                    e.target.style.transform = "translateY(0)";
                    e.target.style.boxShadow = "0 4px 12px rgba(102, 126, 234, 0.3)";
                  }}
                >
                  {idx === 0 ? "👋" : idx === 1 ? "📚" : idx === 2 ? "🎯" : "💻"} {question.substring(0, 40)}...
                </button>
              ))}
            </div>

            <button 
              style={{ 
                width: "100%", 
                padding: "12px", 
                borderRadius: "10px", 
                border: "1px solid #ef4444", 
                background: "rgba(239, 68, 68, 0.15)", 
                color: "#ef4444", 
                fontSize: "15px", 
                fontWeight: "600", 
                cursor: "pointer",
                marginTop: "14px",
                transition: "all 0.3s"
              }} 
              onClick={() => {
                window.speechSynthesis.cancel();
                setIsTalking(false);
              }}
              onMouseOver={(e) => e.target.style.background = "rgba(239, 68, 68, 0.25)"}
              onMouseOut={(e) => e.target.style.background = "rgba(239, 68, 68, 0.15)"}
            >
              ⏹️ Stop Speaking
            </button>
          </div>

          <div style={{ height: "1px", background: "rgba(255,255,255,0.15)", margin: "24px 0" }} />

          {/* Voice Input */}
          <div>
            <h3 style={{ color: "#60a5fa", fontSize: "19px", marginBottom: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "10px" }}>
              🎙️ Voice Answer
            </h3>

            {!isSupported ? (
              <div style={{ 
                background: "rgba(239, 68, 68, 0.15)", 
                border: "1px solid #ef4444",
                borderRadius: "10px",
                padding: "14px",
                color: "#fca5a5",
                fontSize: "14px"
              }}>
                ⚠️ Voice recognition not supported. Use Chrome browser.
              </div>
            ) : (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "14px" }}>
                  <button 
                    style={{ 
                      padding: "14px", 
                      borderRadius: "10px", 
                      border: "none", 
                      background: isListening ? "#ef4444" : "#10b981", 
                      color: "white", 
                      fontSize: "15px", 
                      fontWeight: "600", 
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "8px",
                      boxShadow: isListening ? "0 4px 12px rgba(239, 68, 68, 0.4)" : "0 4px 12px rgba(16, 185, 129, 0.4)"
                    }} 
                    onClick={isListening ? stopListening : startListening}
                  >
                    {isListening ? "⏹️ Stop" : "🎤 Record"}
                  </button>

                  <button 
                    style={{ 
                      padding: "14px", 
                      borderRadius: "10px", 
                      border: "1px solid #374151", 
                      background: "rgba(255,255,255,0.08)", 
                      color: "#9ca3af", 
                      fontSize: "15px", 
                      fontWeight: "600", 
                      cursor: "pointer"
                    }} 
                    onClick={clearTranscript}
                  >
                    🗑️ Clear
                  </button>
                </div>

                {transcript && (
                  <div style={{
                    background: "rgba(16, 185, 129, 0.15)",
                    border: "1px solid #10b981",
                    borderRadius: "10px",
                    padding: "14px",
                    maxHeight: "160px",
                    overflowY: "auto",
                    marginBottom: "14px"
                  }}>
                    <p style={{ color: "#9ca3af", fontSize: "12px", margin: "0 0 8px 0", textTransform: "uppercase", fontWeight: "700" }}>
                      Your Answer:
                    </p>
                    <p style={{ color: "white", fontSize: "14px", lineHeight: "1.7", margin: 0 }}>
                      {transcript}
                    </p>
                  </div>
                )}

                <button 
                  style={{ 
                    width: "100%", 
                    padding: "10px", 
                    borderRadius: "8px", 
                    border: "none", 
                    background: "transparent", 
                    color: "#60a5fa", 
                    fontSize: "13px", 
                    cursor: "pointer",
                    textDecoration: "underline"
                  }} 
                  onClick={() => setShowVoicePanel(!showVoicePanel)}
                >
                  {showVoicePanel ? "Hide" : "Show"} Instructions
                </button>

                {showVoicePanel && (
                  <div style={{
                    background: "rgba(96, 165, 250, 0.15)",
                    border: "1px solid #60a5fa",
                    borderRadius: "10px",
                    padding: "14px",
                    marginTop: "12px"
                  }}>
                    <p style={{ color: "#e5e7eb", fontSize: "13px", lineHeight: "1.8", margin: 0 }}>
                      <strong style={{ color: "#60a5fa" }}>💡 How to use:</strong><br/>
                      1. Click "🎤 Record" and allow mic<br/>
                      2. Speak your answer clearly<br/>
                      3. Click "⏹️ Stop" when done<br/>
                      4. Copy transcript to Streamlit app
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Bottom Info */}
        <div style={{
          position: "absolute",
          bottom: "20px",
          left: "50%",
          transform: "translateX(-50%)",
          background: "rgba(0,0,0,0.9)",
          backdropFilter: "blur(20px)",
          padding: "14px 28px",
          borderRadius: "30px",
          border: "1px solid rgba(255,255,255,0.15)",
          pointerEvents: "auto",
          boxShadow: "0 8px 24px rgba(0,0,0,0.4)"
        }}>
          <p style={{ color: "#9ca3af", fontSize: "14px", margin: 0, textAlign: "center" }}>
            🎓 <strong style={{ color: "white" }}>BCA Final Year Project</strong> | React + Three.js + Streamlit
          </p>
        </div>

      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.7; transform: scale(1.1); }
        }
        
        ::-webkit-scrollbar {
          width: 10px;
        }
        
        ::-webkit-scrollbar-track {
          background: rgba(255,255,255,0.05);
          border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb {
          background: rgba(96, 165, 250, 0.6);
          border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: rgba(96, 165, 250, 0.8);
        }
      `}</style>
    </div>
  );
}

useGLTF.preload("/character.glb");
useGLTF.preload("/animations/Sitting.glb");
useGLTF.preload("/animations/Talking.glb");

ReactDOM.createRoot(document.getElementById("root")).render(<App />);