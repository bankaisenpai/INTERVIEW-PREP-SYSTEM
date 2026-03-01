import React, { useState, useEffect, useRef ,useMemo} from "react";
import ReactDOM from "react-dom/client";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF, useAnimations } from "@react-three/drei";
import * as THREE from "three";

// ═══════════════════════════════════════════════════════════
// AVATAR - YOUR WORKING IDLE START PATTERN
// ═══════════════════════════════════════════════════════════
function Avatar({ isTalking, position = [0, 0.10, -0.0] }) {
  const group = useRef();
  const { scene } = useGLTF("/character.glb");
  const sittingGltf = useGLTF("/animations/Sitting.glb");
  const talkingGltf = useGLTF("/animations/Talking.glb");

 const sitClip = useMemo(() => {
    const clip = sittingGltf.animations?.[0]?.clone();
    if (clip) clip.name = "SITTING";
    return clip || null;
  }, [sittingGltf.animations]);

  const talkClip = useMemo(() => {
    const clip = talkingGltf.animations?.[0]?.clone();
    if (clip) clip.name = "TALKING";
    return clip || null;
  }, [talkingGltf.animations]);

  // ✅ CHANGED: Only pass renamed clips into useAnimations
  const clips = useMemo(() => {
    const arr = [];
    if (sitClip) arr.push(sitClip);
    if (talkClip) arr.push(talkClip);
    return arr;
  }, [sitClip, talkClip]);

  const { actions } = useAnimations(clips, group);

  // ✅ CHANGED: keep "initialize once" pattern
  const initializedRef = useRef(false);
  const currentAction = useRef(null);

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

  // GUARANTEED IDLE START - Initialize ONCE with sitting
  useEffect(() => {
    if (!actions?.SITTING || initializedRef.current) return;

    // Stop anything just in case
    Object.values(actions).forEach((a) => a?.stop());

    actions.SITTING.reset()
      .setLoop(THREE.LoopRepeat, Infinity)
      .setEffectiveTimeScale(0.8)
      .setEffectiveWeight(1)
      .play();

    currentAction.current = actions.SITTING;
    initializedRef.current = true;

    console.log("✅ Avatar initialized: SITTING (IDLE)");
  }, [actions]);

  // ✅ CHANGED: Switch between actions.TALKING and actions.SITTING (no full stop-all needed)
  useEffect(() => {
    if (!initializedRef.current || !actions?.SITTING || !actions?.TALKING) return;

    const next = isTalking ? actions.TALKING : actions.SITTING;
    if (currentAction.current === next) return;

    next.reset()
      .setLoop(THREE.LoopRepeat, Infinity)
      .setEffectiveWeight(1)
      .fadeIn(0.2)
      .play();

    currentAction.current?.fadeOut(0.2);
    currentAction.current = next;
  }, [isTalking, actions]);

  return <primitive ref={group} object={scene} position={position} castShadow />;
}
// ═══════════════════════════════════════════════════════════
// SCENE
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
      <directionalLight position={[4, 8, 5]} intensity={1} castShadow />
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
      
      <mesh position={[0, 0.52, -0.15]} castShadow receiveShadow>
        <boxGeometry args={[0.8, 0.08, 0.7]} />
        <meshStandardMaterial color="#2d3748" roughness={0.5} metalness={0.4} />
      </mesh>
      
      <mesh position={[0, 0.95, -0.45]} castShadow>
        <boxGeometry args={[0.8, 0.9, 0.08]} />
        <meshStandardMaterial color="#2d3748" roughness={0.5} metalness={0.4} />
      </mesh>
      
      <mesh position={[0, 2.5, -4]} receiveShadow>
        <planeGeometry args={[12, 5]} />
        <meshStandardMaterial color="#1e293b" roughness={0.9} />
      </mesh>
      
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
                <p style={{ color: "#9ca3af", fontSize: "13px", margin: 0 }}>Professional Interview Simulation</p>
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