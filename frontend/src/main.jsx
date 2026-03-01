import React, { useState, useEffect, useRef ,useMemo} from "react";
import ReactDOM from "react-dom/client";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF, useAnimations } from "@react-three/drei";
import * as THREE from "three";

// ═══════════════════════════════════════════════════════════
// AVATAR - GUARANTEED IDLE START (YOUR WORKING PATTERN)
// ═══════════════════════════════════════════════════════════
function Avatar({ isTalking, position = [0, 0.10, 0.1] }) {
  const group = useRef();
  const initializedRef = useRef(false);
  const currentAction = useRef(null);

  const { scene } = useGLTF("/character.glb");
  const sittingGltf = useGLTF("/animations/Sitting.glb");
  const talkingGltf = useGLTF("/animations/Talking.glb");

  // ✅ Fix: clone + rename clips so actions don't overwrite each other
  const sitClip = useMemo(() => {
    const c = sittingGltf.animations?.[0]?.clone();
    if (c) c.name = "SITTING";
    return c || null;
  }, [sittingGltf.animations]);

  const talkClip = useMemo(() => {
    const c = talkingGltf.animations?.[0]?.clone();
    if (c) c.name = "TALKING";
    return c || null;
  }, [talkingGltf.animations]);

  const clips = useMemo(() => [sitClip, talkClip].filter(Boolean), [sitClip, talkClip]);
  const { actions } = useAnimations(clips, group);

  // Character scaling (same logic)
  useEffect(() => {
    if (!scene) return;
    const box = new THREE.Box3().setFromObject(scene);
    const size = box.getSize(new THREE.Vector3());
    const targetHeight = 3;
    let scale = targetHeight / (size.y || 1);
    scale = Math.min(scale, 1.3);
    scale = Math.max(scale, 0.2);
    scene.scale.set(scale, scale, scale);
    const newBox = new THREE.Box3().setFromObject(scene);
    const newCenter = newBox.getCenter(new THREE.Vector3());
    scene.position.set(-newCenter.x, -newBox.min.y, -newCenter.z - 0.03);
  }, [scene]);

  // ✅ GUARANTEED IDLE START: play SITTING once
  useEffect(() => {
    if (!actions?.SITTING || initializedRef.current) return;

    Object.values(actions).forEach((a) => {
      a?.stop();
      a?.reset();
    });

    actions.SITTING
      .reset()
      .setLoop(THREE.LoopRepeat, Infinity)
      .setEffectiveTimeScale(0.8)
      .setEffectiveWeight(1.0)
      .play();

    currentAction.current = actions.SITTING;
    initializedRef.current = true;
    console.log("✅ Avatar IDLE (SITTING)");
  }, [actions]);

  // ✅ Switch between SITTING and TALKING
  useEffect(() => {
    if (!initializedRef.current || !actions?.SITTING || !actions?.TALKING) return;

    const next = isTalking ? actions.TALKING : actions.SITTING;
    if (currentAction.current === next) return;

    next
      .reset()
      .setLoop(THREE.LoopRepeat, Infinity)
      .setEffectiveWeight(1.0)
      .fadeIn(0.2)
      .play();

    currentAction.current?.fadeOut(0.2);
    currentAction.current = next;

    console.log(isTalking ? "🗣️ TALKING" : "💺 SITTING");
  }, [isTalking, actions]);

  return <primitive ref={group} object={scene} position={position} castShadow />;
}

// ═══════════════════════════════════════════════════════════
// ENHANCED OFFICE SCENE WITH DECORATIONS
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
      
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <directionalLight position={[4, 8, 5]} intensity={1} castShadow shadow-mapSize={[2048, 2048]} />
      <directionalLight position={[-4, 4, -3]} intensity={0.5} color="#9bb5ff" />
      <directionalLight position={[0, 5, -8]} intensity={0.7} />
      <spotLight position={[0, 3.5, 4]} angle={0.5} penumbra={0.5} intensity={0.4} color="#fff8f0" />
      
      {/* Floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[15, 15]} />
        <meshStandardMaterial color="#2d3748" roughness={0.85} />
      </mesh>
      <gridHelper args={[12, 24, "#3d4a5c", "#2a3441"]} position={[0, 0.005, 0]} />
      
      {/* ===== DESK ===== */}
      <mesh position={[0, 0.76, 0.5]} castShadow receiveShadow>
        <boxGeometry args={[2.0, 0.06, 0.9]} />
        <meshStandardMaterial color="#4a3728" roughness={0.6} />
      </mesh>
      
      {/* Desk legs */}
      {[[-0.9, 0.38, 0.8], [0.9, 0.38, 0.8], [-0.9, 0.38, 0.2], [0.9, 0.38, 0.2]].map((pos, i) => (
        <mesh key={`leg-${i}`} position={pos} castShadow>
          <cylinderGeometry args={[0.03, 0.03, 0.76, 12]} />
          <meshStandardMaterial color="#2c3e50" roughness={0.4} metalness={0.7} />
        </mesh>
      ))}
      
      {/* ===== BOOKS STACK ON DESK ===== */}
      {/* Book 1 - Bottom */}
      <mesh position={[-0.6, 0.81, 0.6]} castShadow>
        <boxGeometry args={[0.25, 0.04, 0.35]} />
        <meshStandardMaterial color="#8b0000" roughness={0.7} />
      </mesh>
      
      {/* Book 2 - Middle */}
      <mesh position={[-0.6, 0.85, 0.6]} castShadow>
        <boxGeometry args={[0.24, 0.04, 0.32]} />
        <meshStandardMaterial color="#1e3a8a" roughness={0.7} />
      </mesh>
      
      {/* Book 3 - Top */}
      <mesh position={[-0.6, 0.89, 0.6]} castShadow>
        <boxGeometry args={[0.26, 0.04, 0.30]} />
        <meshStandardMaterial color="#065f46" roughness={0.7} />
      </mesh>
      
      {/* Book 4 - Leaning */}
      <mesh position={[-0.45, 0.83, 0.6]} rotation={[0, 0, 0.3]} castShadow>
        <boxGeometry args={[0.22, 0.04, 0.30]} />
        <meshStandardMaterial color="#78350f" roughness={0.7} />
      </mesh>
      
      {/* ===== LAPTOP ON DESK ===== */}
      {/* Laptop base */}
      <mesh position={[0.15, 0.80, 0.45]} castShadow>
        <boxGeometry args={[0.4, 0.02, 0.28]} />
        <meshStandardMaterial color="#1e293b" metalness={0.6} />
      </mesh>
      
      {/* Laptop screen */}
      <mesh position={[0.15, 0.96, 0.32]} rotation={[-0.25, 0, 0]} castShadow>
        <boxGeometry args={[0.4, 0.3, 0.015]} />
        <meshStandardMaterial color="#1e293b" metalness={0.6} />
      </mesh>
      
      {/* Laptop screen display */}
      <mesh position={[0.15, 0.96, 0.315]} rotation={[-0.25, 0, 0]}>
        <planeGeometry args={[0.36, 0.26]} />
        <meshBasicMaterial color="#3b82f6" />
      </mesh>
      
      {/* ===== COFFEE MUG ===== */}
      <mesh position={[0.65, 0.82, 0.55]} castShadow>
        <cylinderGeometry args={[0.04, 0.04, 0.08, 16]} />
        <meshStandardMaterial color="#7f1d1d" roughness={0.3} />
      </mesh>
      
      {/* Coffee inside */}
      <mesh position={[0.65, 0.85, 0.55]}>
        <cylinderGeometry args={[0.038, 0.038, 0.01, 16]} />
        <meshStandardMaterial color="#3e2723" />
      </mesh>
      
      {/* ===== CHAIR (CANDIDATE) ===== */}
      <mesh position={[0, 0.52, -0.15]} castShadow receiveShadow>
        <boxGeometry args={[0.8, 0.08, 0.7]} />
        <meshStandardMaterial color="#2d3748" roughness={0.5} metalness={0.4} />
      </mesh>
      
      <mesh position={[0, 0.95, -0.45]} castShadow>
        <boxGeometry args={[0.8, 0.9, 0.08]} />
        <meshStandardMaterial color="#2d3748" roughness={0.5} metalness={0.4} />
      </mesh>
      
      {/* ===== WINDOW ON SIDE WALL ===== */}
      {/* Window frame */}
      <mesh position={[-3.5, 2.0, 0]} rotation={[0, Math.PI / 2, 0]} castShadow>
        <boxGeometry args={[2.0, 1.5, 0.08]} />
        <meshStandardMaterial color="#2c3e50" roughness={0.3} metalness={0.6} />
      </mesh>
      
      {/* Window glass (4 panes) */}
      {[
        [-3.45, 2.0, -0.5],
        [-3.45, 2.0, 0.5],
        [-3.45, 1.25, -0.5],
        [-3.45, 1.25, 0.5]
      ].map((pos, i) => (
        <mesh key={`window-${i}`} position={pos} rotation={[0, Math.PI / 2, 0]}>
          <planeGeometry args={[0.9, 0.7]} />
          <meshStandardMaterial 
            color="#87ceeb" 
            transparent 
            opacity={0.4} 
            metalness={0.9} 
            roughness={0.1} 
          />
        </mesh>
      ))}
      
      {/* Window cross bars */}
      <mesh position={[-3.47, 2.0, 0]} rotation={[0, Math.PI / 2, 0]}>
        <boxGeometry args={[2.0, 0.03, 0.02]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      <mesh position={[-3.47, 2.0, 0]} rotation={[Math.PI / 2, Math.PI / 2, 0]}>
        <boxGeometry args={[1.5, 0.03, 0.02]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      
      {/* ===== POTTED PLANT ===== */}
      {/* Pot */}
      <mesh position={[-2.2, 0.125, -1.5]} castShadow>
        <cylinderGeometry args={[0.15, 0.18, 0.25, 16]} />
        <meshStandardMaterial color="#8b4513" roughness={0.8} />
      </mesh>
      
      {/* Soil */}
      <mesh position={[-2.2, 0.25, -1.5]}>
        <cylinderGeometry args={[0.14, 0.14, 0.01, 16]} />
        <meshStandardMaterial color="#4a2511" />
      </mesh>
      
      {/* Plant leaves (5 leaves) */}
      {[...Array(5)].map((_, i) => {
        const angle = (i / 5) * Math.PI * 2;
        const radius = 0.1;
        return (
          <mesh 
            key={`leaf-${i}`} 
            position={[
              -2.2 + Math.cos(angle) * radius,
              0.35 + i * 0.1,
              -1.5 + Math.sin(angle) * radius
            ]}
            rotation={[0, angle, 0]}
          >
            <sphereGeometry args={[0.12, 8, 8]} />
            <meshStandardMaterial color="#2d5016" roughness={0.7} />
          </mesh>
        );
      })}
      
      {/* ===== BOOKSHELF ===== */}
      {/* Shelf structure */}
      <mesh position={[2.5, 0.75, -1.8]} castShadow>
        <boxGeometry args={[0.5, 1.5, 0.35]} />
        <meshStandardMaterial color="#3d2b1f" roughness={0.8} />
      </mesh>
      
      {/* Books on shelf (8 books in 2 rows) */}
      {[...Array(8)].map((_, i) => {
        const colors = ["#7f1d1d", "#1e3a8a", "#065f46", "#78350f"];
        const row = Math.floor(i / 4);
        const col = i % 4;
        return (
          <mesh 
            key={`shelf-book-${i}`} 
            position={[
              2.5 - 0.18 + col * 0.09,
              0.35 + row * 0.4,
              -1.8
            ]}
            castShadow
          >
            <boxGeometry args={[0.07, 0.18, 0.22]} />
            <meshStandardMaterial color={colors[i % colors.length]} roughness={0.7} />
          </mesh>
        );
      })}
      
      {/* ===== PICTURE FRAME ON WALL ===== */}
      <mesh position={[0, 2.2, -3.9]} castShadow>
        <boxGeometry args={[0.8, 0.6, 0.03]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      
      {/* Picture (abstract art) */}
      <mesh position={[0, 2.2, -3.88]}>
        <planeGeometry args={[0.7, 0.5]} />
        <meshStandardMaterial color="#4ade80" />
      </mesh>
      
      {/* ===== WALLS ===== */}
      {/* Back wall */}
      <mesh position={[0, 2.5, -4]} receiveShadow>
        <planeGeometry args={[12, 5]} />
        <meshStandardMaterial color="#1e293b" roughness={0.9} />
      </mesh>
      
      {/* Left wall */}
      <mesh position={[-6, 2.5, 0]} rotation={[0, Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[8, 5]} />
        <meshStandardMaterial color="#141b2d" roughness={0.9} />
      </mesh>
      
      {/* Right wall */}
      <mesh position={[6, 2.5, 0]} rotation={[0, -Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[8, 5]} />
        <meshStandardMaterial color="#141b2d" roughness={0.9} />
      </mesh>
      
      {/* ===== CEILING LAMP ===== */}
      <mesh position={[0, 4.5, 0]}>
        <cylinderGeometry args={[0.15, 0.25, 0.3, 16]} />
        <meshStandardMaterial color="#fef3c7" emissive="#fef3c7" emissiveIntensity={0.5} />
      </mesh>
      
      {/* Avatar */}
      <Avatar isTalking={isTalking} />
    </>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════════
function App() {
  const [isTalking, setIsTalking] = useState(false);  // STARTS FALSE = GUARANTEED IDLE
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <div 
      ref={containerRef}
      style={{ 
        width: "100vw", 
        height: "100vh", 
        position: "relative", 
        overflow: "hidden",
        background: "#000"
      }}
    >
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
        
        {!isFullscreen && (
          <div style={{ 
            position: "absolute", 
            top: 0, 
            left: 0, 
            right: 0, 
            height: "70px", 
            background: "rgba(0,0,0,0.95)", 
            backdropFilter: "blur(20px)", 
            display: "flex", 
            alignItems: "center", 
            justifyContent: "space-between", 
            padding: "0 30px",
            pointerEvents: "auto",
            borderBottom: "1px solid rgba(255,255,255,0.1)"
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
                fontSize: "26px"
              }}>
                🎤
              </div>
              <div>
                <h1 style={{ color: "white", fontSize: "22px", fontWeight: "700", margin: 0 }}>
                  AI-Powered Interview Preparation System
                </h1>
                <p style={{ color: "#9ca3af", fontSize: "13px", margin: 0 }}>Professional Office Environment</p>
              </div>
            </div>
            
            <button
              onClick={toggleFullscreen}
              style={{
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                color: "white",
                border: "none",
                padding: "12px 24px",
                borderRadius: "8px",
                fontSize: "15px",
                fontWeight: "600",
                cursor: "pointer",
                boxShadow: "0 4px 12px rgba(102, 126, 234, 0.4)",
                transition: "transform 0.2s"
              }}
              onMouseOver={(e) => e.target.style.transform = "translateY(-2px)"}
              onMouseOut={(e) => e.target.style.transform = "translateY(0)"}
            >
              🖥️ Fullscreen
            </button>
          </div>
        )}

        <div style={{
          position: "absolute",
          bottom: "20px",
          left: "50%",
          transform: "translateX(-50%)",
          background: "rgba(0,0,0,0.95)",
          backdropFilter: "blur(20px)",
          padding: "14px 28px",
          borderRadius: "30px",
          border: "1px solid rgba(255,255,255,0.15)",
          pointerEvents: "none",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          boxShadow: "0 8px 24px rgba(0,0,0,0.5)"
        }}>
          <div style={{
            width: "14px",
            height: "14px",
            borderRadius: "50%",
            background: isTalking ? "#10b981" : "#6b7280",
            boxShadow: isTalking ? "0 0 15px #10b981" : "none",
            animation: isTalking ? "pulse 1.5s infinite" : "none"
          }} />
          <span style={{ color: "white", fontSize: "15px", fontWeight: "600" }}>
            {isTalking ? "🗣️ AI Interviewer Speaking" : "💺 Ready for Interview"}
          </span>
        </div>

        {isFullscreen && (
          <button
            onClick={toggleFullscreen}
            style={{
              position: "absolute",
              top: "20px",
              right: "20px",
              background: "rgba(0,0,0,0.9)",
              border: "1px solid rgba(255,255,255,0.2)",
              color: "white",
              padding: "12px 20px",
              borderRadius: "8px",
              fontSize: "16px",
              fontWeight: "600",
              cursor: "pointer",
              pointerEvents: "auto"
            }}
          >
            ✕ Exit
          </button>
        )}

      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.2); }
        }
      `}</style>
    </div>
  );
}

useGLTF.preload("/character.glb");
useGLTF.preload("/animations/Sitting.glb");
useGLTF.preload("/animations/Talking.glb");

ReactDOM.createRoot(document.getElementById("root")).render(<App />);