// Scene3D.jsx - COMPLETE FIXED VERSION
import React, { useState, useEffect, useRef, useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF, useAnimations, useTexture } from "@react-three/drei";
import * as THREE from "three";

// ═══════════════════════════════════════════════════════════
// AVATAR WITH TALKING ANIMATION
// ═══════════════════════════════════════════════════════════
function Avatar({ isTalking, position = [0, 0.10, 0.1] }) {
  const group = useRef();
  const initializedRef = useRef(false);
  const currentAction = useRef(null);

  const { scene } = useGLTF("/character.glb");
  const sittingGltf = useGLTF("/animations/Sitting.glb");
  const talkingGltf = useGLTF("/animations/Talking.glb");

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

  // Character scaling
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

  // Start with SITTING animation
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
  }, [actions]);

  // Switch between SITTING and TALKING
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
  }, [isTalking, actions]);

  return <primitive ref={group} object={scene} position={position} castShadow />;
}

// ═══════════════════════════════════════════════════════════
// SCENE COMPONENTS - FULL OFFICE ENVIRONMENT
// ═══════════════════════════════════════════════════════════
function WallArt() {
  const art = useTexture("/textures/wallart.png");
  if ("colorSpace" in art) art.colorSpace = THREE.SRGBColorSpace;
  if ("encoding" in art) art.encoding = THREE.sRGBEncoding;

  return (
    <group position={[0, 2.2, -3.9]}>
      <mesh castShadow>
        <boxGeometry args={[0.9, 0.7, 0.04]} />
        <meshStandardMaterial color="#0f172a" roughness={0.5} metalness={0.2} />
      </mesh>
      <mesh position={[0, 0, 0.025]}>
        <planeGeometry args={[0.78, 0.58]} />
        <meshStandardMaterial map={art} roughness={0.8} />
      </mesh>
      <mesh position={[0, 0, 0.028]}>
        <planeGeometry args={[0.8, 0.6]} />
        <meshPhysicalMaterial
          transparent
          opacity={0.12}
          roughness={0.08}
          clearcoat={1}
          clearcoatRoughness={0.1}
          color="#ffffff"
        />
      </mesh>
    </group>
  );
}

function Desk() {
  return (
    <group position={[0, 0, 0]}>
      {/* Desk top */}
      <mesh position={[0, 0.9, 0]} castShadow receiveShadow>
        <boxGeometry args={[2.8, 0.08, 1.2]} />
        <meshStandardMaterial color="#3d2817" roughness={0.6} metalness={0.1} />
      </mesh>
      
      {/* Desk legs */}
      <mesh position={[-1.2, 0.45, 0.4]} castShadow>
        <boxGeometry args={[0.08, 0.9, 0.08]} />
        <meshStandardMaterial color="#2d1f12" roughness={0.7} />
      </mesh>
      <mesh position={[1.2, 0.45, 0.4]} castShadow>
        <boxGeometry args={[0.08, 0.9, 0.08]} />
        <meshStandardMaterial color="#2d1f12" roughness={0.7} />
      </mesh>
      <mesh position={[-1.2, 0.45, -0.4]} castShadow>
        <boxGeometry args={[0.08, 0.9, 0.08]} />
        <meshStandardMaterial color="#2d1f12" roughness={0.7} />
      </mesh>
      <mesh position={[1.2, 0.45, -0.4]} castShadow>
        <boxGeometry args={[0.08, 0.9, 0.08]} />
        <meshStandardMaterial color="#2d1f12" roughness={0.7} />
      </mesh>
    </group>
  );
}

function Chair() {
  return (
    <group position={[0, 0.32, 0.5]}>
      {/* Seat */}
      <mesh position={[0, 0, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.55, 0.08, 0.55]} />
        <meshStandardMaterial color="#1e293b" roughness={0.8} />
      </mesh>
      
      {/* Backrest */}
      <mesh position={[0, 0.35, -0.23]} castShadow>
        <boxGeometry args={[0.55, 0.7, 0.08]} />
        <meshStandardMaterial color="#1e293b" roughness={0.8} />
      </mesh>
      
      {/* Center pole */}
      <mesh position={[0, -0.15, 0]} castShadow>
        <cylinderGeometry args={[0.04, 0.04, 0.3, 16]} />
        <meshStandardMaterial color="#374151" roughness={0.6} metalness={0.3} />
      </mesh>
      
      {/* Base */}
      <mesh position={[0, -0.31, 0]} rotation={[0, Math.PI / 5, 0]} castShadow>
        <cylinderGeometry args={[0.28, 0.28, 0.04, 5]} />
        <meshStandardMaterial color="#374151" roughness={0.6} metalness={0.3} />
      </mesh>
    </group>
  );
}

function Window() {
  return (
    <group position={[-3.5, 2, -1]}>
      {/* Window frame */}
      <mesh castShadow>
        <boxGeometry args={[0.1, 2, 1.6]} />
        <meshStandardMaterial color="#1e293b" roughness={0.7} />
      </mesh>
      
      {/* Glass panes */}
      <mesh position={[0.06, 0.5, 0]}>
        <planeGeometry args={[1.5, 0.9]} />
        <meshPhysicalMaterial
          color="#87ceeb"
          transparent
          opacity={0.3}
          roughness={0.1}
          metalness={0.1}
          clearcoat={1}
          clearcoatRoughness={0.1}
        />
      </mesh>
      
      <mesh position={[0.06, -0.5, 0]}>
        <planeGeometry args={[1.5, 0.9]} />
        <meshPhysicalMaterial
          color="#87ceeb"
          transparent
          opacity={0.3}
          roughness={0.1}
          metalness={0.1}
          clearcoat={1}
          clearcoatRoughness={0.1}
        />
      </mesh>
    </group>
  );
}

function Bookshelf() {
  return (
    <group position={[3, 1.2, -2.5]}>
      {/* Shelves */}
      {[0, 0.6, 1.2].map((y, i) => (
        <mesh key={i} position={[0, y, 0]} castShadow receiveShadow>
          <boxGeometry args={[0.8, 0.04, 0.35]} />
          <meshStandardMaterial color="#4a3728" roughness={0.7} />
        </mesh>
      ))}
      
      {/* Back panel */}
      <mesh position={[0, 0.6, -0.16]} castShadow>
        <boxGeometry args={[0.8, 1.24, 0.04]} />
        <meshStandardMaterial color="#3d2817" roughness={0.7} />
      </mesh>
      
      {/* Side panels */}
      <mesh position={[-0.38, 0.6, 0]} castShadow>
        <boxGeometry args={[0.04, 1.24, 0.35]} />
        <meshStandardMaterial color="#3d2817" roughness={0.7} />
      </mesh>
      <mesh position={[0.38, 0.6, 0]} castShadow>
        <boxGeometry args={[0.04, 1.24, 0.35]} />
        <meshStandardMaterial color="#3d2817" roughness={0.7} />
      </mesh>
      
      {/* Books */}
      {[-0.2, -0.05, 0.1, 0.25].map((x, i) => (
        <mesh key={i} position={[x, 0.22, 0]} castShadow>
          <boxGeometry args={[0.08, 0.3, 0.22]} />
          <meshStandardMaterial 
            color={['#c0392b', '#2980b9', '#27ae60', '#8e44ad'][i]} 
            roughness={0.8} 
          />
        </mesh>
      ))}
    </group>
  );
}

function Floor() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
      <planeGeometry args={[30, 30]} />
      <meshStandardMaterial 
        color="#1a1f2e" 
        roughness={0.9} 
        metalness={0.1} 
      />
    </mesh>
  );
}

function Walls() {
  return (
    <>
      {/* Back wall */}
      <mesh position={[0, 3, -4]} receiveShadow>
        <planeGeometry args={[20, 8]} />
        <meshStandardMaterial color="#0f1419" roughness={0.9} />
      </mesh>
      
      {/* Left wall */}
      <mesh position={[-4, 3, 0]} rotation={[0, Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[20, 8]} />
        <meshStandardMaterial color="#0f1419" roughness={0.9} />
      </mesh>
      
      {/* Right wall */}
      <mesh position={[4, 3, 0]} rotation={[0, -Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[20, 8]} />
        <meshStandardMaterial color="#0f1419" roughness={0.9} />
      </mesh>
    </>
  );
}

function PlantPot() {
  return (
    <group position={[-2, 0, 1.5]}>
      {/* Pot */}
      <mesh castShadow>
        <cylinderGeometry args={[0.18, 0.15, 0.3, 16]} />
        <meshStandardMaterial color="#8b4513" roughness={0.8} />
      </mesh>
      
      {/* Soil */}
      <mesh position={[0, 0.13, 0]}>
        <cylinderGeometry args={[0.17, 0.17, 0.04, 16]} />
        <meshStandardMaterial color="#3e2723" roughness={1} />
      </mesh>
      
      {/* Plant stems */}
      {[0, Math.PI / 3, -Math.PI / 3].map((angle, i) => (
        <group key={i} rotation={[0, angle, 0]}>
          <mesh position={[0, 0.4, 0]} castShadow>
            <cylinderGeometry args={[0.02, 0.02, 0.5, 8]} />
            <meshStandardMaterial color="#2d5016" roughness={0.9} />
          </mesh>
          
          {/* Leaves */}
          <mesh position={[0.1, 0.5, 0]} rotation={[0, 0, Math.PI / 6]} castShadow>
            <boxGeometry args={[0.15, 0.3, 0.01]} />
            <meshStandardMaterial color="#4caf50" roughness={0.8} />
          </mesh>
          <mesh position={[-0.1, 0.55, 0]} rotation={[0, 0, -Math.PI / 6]} castShadow>
            <boxGeometry args={[0.15, 0.3, 0.01]} />
            <meshStandardMaterial color="#4caf50" roughness={0.8} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

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
      <directionalLight 
        position={[4, 8, 5]} 
        intensity={1} 
        castShadow 
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
      />
      <directionalLight position={[-4, 4, -3]} intensity={0.5} color="#9bb5ff" />
      <directionalLight position={[0, 5, -8]} intensity={0.7} />
      <spotLight 
        position={[0, 3.5, 4]} 
        angle={0.5} 
        penumbra={0.5} 
        intensity={0.4} 
        color="#fff8f0" 
      />
      
      {/* Scene objects */}
      <Floor />
      <Walls />
      <Desk />
      <Chair />
      <Window />
      <Bookshelf />
      <WallArt />
      <PlantPot />
      <Avatar isTalking={isTalking} />
    </>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN SCENE COMPONENT
// ═══════════════════════════════════════════════════════════
function Scene3D() {
  const [isTalking, setIsTalking] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);

  // Listen for messages from Streamlit parent window
  useEffect(() => {
    const handleMessage = (event) => {
      if (event.data && event.data.type === 'SET_TALKING') {
        console.log('📨 Received talking state:', event.data.value);
        setIsTalking(event.data.value);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

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
        width: "100%", 
        height: "100%", 
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

      {/* Fullscreen button */}
      <button
        onClick={toggleFullscreen}
        style={{
          position: "absolute",
          top: "20px",
          right: "20px",
          background: "rgba(0,0,0,0.9)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255,255,255,0.2)",
          color: "white",
          padding: "12px 20px",
          borderRadius: "8px",
          fontSize: "14px",
          fontWeight: "600",
          cursor: "pointer",
          pointerEvents: "auto",
          zIndex: 20,
          display: "flex",
          alignItems: "center",
          gap: "8px"
        }}
      >
        {isFullscreen ? "✕ Exit Fullscreen" : "⛶ Fullscreen"}
      </button>

      {/* Status indicator */}
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
        boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
        zIndex: 10
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

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.2); }
        }
      `}</style>
    </div>
  );
}

// Preload assets
useGLTF.preload("/character.glb");
useGLTF.preload("/animations/Sitting.glb");
useGLTF.preload("/animations/Talking.glb");

export default Scene3D;