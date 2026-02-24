import React, { useState, useEffect, useRef } from "react";
import ReactDOM from "react-dom/client";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF, useAnimations } from "@react-three/drei";
import * as THREE from "three";

// ═══════════════════════════════════════════════════════════
// AVATAR COMPONENT
// ═══════════════════════════════════════════════════════════
function Avatar({ isTalking, position = [0, 0.16, -0.18] }) {
  const group = useRef();
  const { scene } = useGLTF("/character.glb");
  const sitting = useGLTF("/animations/Sitting.glb");
  const talking = useGLTF("/animations/Talking.glb");

  const animations = [...sitting.animations, ...talking.animations];
  const { actions } = useAnimations(animations, group);

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
    scene.position.set(-newCenter.x, -newBox.min.y, -newCenter.z);
  }, [scene]);

  useEffect(() => {
    if (!actions) return;
    Object.values(actions).forEach((action) => action.stop());
    if (isTalking && talking.animations[0]) {
      actions[talking.animations[0].name]?.reset().setLoop(THREE.LoopRepeat, Infinity).play();
    } else if (sitting.animations[0]) {
      actions[sitting.animations[0].name]?.reset().setLoop(THREE.LoopRepeat, Infinity).play();
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
  const [isRecording, setIsRecording] = useState(false);

  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.onstart = () => setIsTalking(true);
    utterance.onend = () => setIsTalking(false);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative", overflow: "hidden" }}>
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
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "60px", background: "rgba(0,0,0,0.8)", backdropFilter: "blur(10px)", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", pointerEvents: "auto" }}>
          <h1 style={{ color: "white", fontSize: "20px", fontWeight: "bold" }}>🎤 AI Interview Prep</h1>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "white", fontSize: "14px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: isTalking ? "#10b981" : "#6b7280" }} />
            <span>{isTalking ? "Speaking..." : "Ready"}</span>
          </div>
        </div>
        <div style={{ position: "absolute", top: "80px", right: "20px", width: "280px", background: "rgba(0,0,0,0.85)", backdropFilter: "blur(10px)", borderRadius: "12px", padding: "20px", pointerEvents: "auto" }}>
          <h3 style={{ color: "#60a5fa", fontSize: "16px", marginBottom: "12px" }}>⚙️ Settings</h3>
          <div style={{ marginBottom: "12px" }}>
            <label style={{ color: "#9ca3af", fontSize: "13px", display: "block", marginBottom: "6px" }}>Role:</label>
            <select style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #374151", background: "#1f2937", color: "white", fontSize: "14px" }} value={jobRole} onChange={(e) => setJobRole(e.target.value)}>
              <option>Data Scientist</option>
              <option>ML Engineer</option>
              <option>Software Engineer</option>
            </select>
          </div>
          <div style={{ marginBottom: "12px" }}>
            <label style={{ color: "#9ca3af", fontSize: "13px", display: "block", marginBottom: "6px" }}>Difficulty:</label>
            <select style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #374151", background: "#1f2937", color: "white", fontSize: "14px" }} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option>Beginner</option>
              <option>Intermediate</option>
              <option>Advanced</option>
              <option>FAANG</option>
            </select>
          </div>
          <h3 style={{ color: "#60a5fa", fontSize: "16px", marginTop: "20px", marginBottom: "12px" }}>🎙️ Controls</h3>
          <button style={{ width: "100%", padding: "12px", borderRadius: "8px", border: "none", background: "#3b82f6", color: "white", fontSize: "14px", fontWeight: "600", cursor: "pointer", marginBottom: "10px" }} onClick={() => speak("Hello! Welcome to your interview. Can you tell me about your experience?")}>
            Ask Question
          </button>
          <button style={{ width: "100%", padding: "12px", borderRadius: "8px", border: "none", background: isRecording ? "#ef4444" : "#3b82f6", color: "white", fontSize: "14px", fontWeight: "600", cursor: "pointer" }} onClick={() => setIsRecording(!isRecording)}>
            {isRecording ? "⏹️ Stop" : "🎤 Record"}
          </button>
        </div>
      </div>
    </div>
  );
}
useGLTF.preload("/character.glb");
useGLTF.preload("/animations/Sitting.glb");
useGLTF.preload("/animations/Talking.glb");

ReactDOM.createRoot(document.getElementById("root")).render(
  <App />
);