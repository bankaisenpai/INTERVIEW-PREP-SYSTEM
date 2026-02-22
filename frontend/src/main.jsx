import React from "react";
import ReactDOM from "react-dom/client";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF, useAnimations } from "@react-three/drei";
import { useEffect, useRef } from "react";
import * as THREE from "three";
import { Environment } from "@react-three/drei";
import { ContactShadows } from "@react-three/drei";

function Avatar({ mode, position = [0, 0, 0], rotation = [0, 0, 0] }) {
  const group = useRef();
  const { scene } = useGLTF("/character.glb");

  const sitting = useGLTF("/animations/Sitting.glb");
  const talking = useGLTF("/animations/Talking.glb");

  const animations = [...sitting.animations, ...talking.animations];
  const { actions } = useAnimations(animations, group);

  // 🔥 PROPER AUTO SCALE + CENTER (Like your HTML file)
  useEffect(() => {
    if (!scene) return;

    const box = new THREE.Box3().setFromObject(scene);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());

    const targetHeight = 1.3; // same idea as HTML
    const scale = targetHeight / size.y;

    scene.scale.set(scale, scale, scale);

    box.setFromObject(scene);
    const newCenter = box.getCenter(new THREE.Vector3());

    scene.position.set(-newCenter.x, -box.min.y, -newCenter.z);
  }, [scene]);

  useEffect(() => {
    if (!actions) return;

    Object.values(actions).forEach((a) => a.stop());

    if (mode === "talking" && talking.animations[0]) {
      actions[talking.animations[0].name]
        ?.reset()
        .setLoop(THREE.LoopRepeat, Infinity)
        .play();
    } else if (sitting.animations[0]) {
      actions[sitting.animations[0].name]
        ?.reset()
        .setLoop(THREE.LoopRepeat, Infinity)
        .play();
    }
  }, [mode, actions, sitting, talking]);

  return (
    <primitive
      ref={group}
      object={scene}
      position={position}
      rotation={rotation}
      castShadow
    />
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <div style={{ width: "100vw", height: "100vh" }}>
      <Canvas
        shadows
        camera={{ position: [0, 1.6, 4.2], fov: 45 }}
        gl={{ toneMapping: THREE.ACESFilmicToneMapping }}
      >
        {/* Background + Fog */}
        <color attach="background" args={["#1a1f35"]} />
        <fog attach="fog" args={["#1a1f35", 5, 20]} />
        
        <mesh position={[-6, 2.5, 0]} rotation={[0, Math.PI / 2, 0]} receiveShadow>
  <planeGeometry args={[8, 5]} />
  <meshStandardMaterial color="#141b2d" roughness={0.9} />
</mesh>
      
       <mesh position={[6, 2.5, 0]} rotation={[0, -Math.PI / 2, 0]} receiveShadow>
  <planeGeometry args={[8, 5]} />
  <meshStandardMaterial color="#141b2d" roughness={0.9} />
</mesh>

        <OrbitControls
  target={[0, 1, 0]}
  enableDamping
  dampingFactor={0.06}
  minDistance={3}
  maxDistance={6}
  minPolarAngle={Math.PI / 3}       // limit looking down
  maxPolarAngle={Math.PI / 1.8}     // limit looking up
  minAzimuthAngle={-Math.PI / 4}    // limit left rotation
  maxAzimuthAngle={Math.PI / 4}     // limit right rotation
  enablePan={false}
/>

        {/* Lights */}
        <ambientLight intensity={0.6} />

        <directionalLight
          position={[4, 8, 5]}
          intensity={1.3}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />

        <directionalLight position={[-4, 4, -3]} intensity={0.5} />
        <directionalLight position={[0, 5, -8]} intensity={0.7} />

        {/* Floor */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[15, 15]} />
          <meshStandardMaterial color="#2d3748" roughness={0.85} />
        </mesh>

        <mesh position={[0, 2.5, 4]} rotation={[0, Math.PI, 0]}>
  <planeGeometry args={[12, 5]} />
  <meshStandardMaterial color="#111827" roughness={0.9} />
</mesh>

        <mesh position={[0, 2.8, 3.95]}>
  <planeGeometry args={[3, 1]} />
  <meshStandardMaterial color="#0f172a" />
</mesh>

<mesh position={[0, 2.8, 3.94]}>
  <planeGeometry args={[2.6, 0.7]} />
  <meshBasicMaterial color="#3b82f6" />
</mesh>

      <meshStandardMaterial
  color="#1e293b"
  roughness={0.1}
  metalness={0.2}
  transparent
  opacity={0.6}
/>

        {/* 🔥 STEP 4 — Cinematic Back Wall */}
        <mesh position={[0, 2.5, -4]} receiveShadow>
          <planeGeometry args={[12, 5]} />
          <meshStandardMaterial color="#1e293b" roughness={0.9} />
        </mesh>
          
        {/* Poster Frame */}
<mesh position={[0, 3.2, -3.95]}>
  <planeGeometry args={[2, 1]} />
  <meshStandardMaterial color="#0f172a" />
</mesh>

{/* Poster Content */}
<mesh position={[0, 3.2, -3.94]}>
  <planeGeometry args={[1.8, 0.8]} />
  <meshBasicMaterial color="#3b82f6" />
</mesh>

<spotLight
  position={[0, 3.5, 4]}
  angle={0.4}
  penumbra={0.5}
  intensity={0.6}
/>
<gridHelper args={[12, 24, "#2a3441", "#1e293b"]} position={[0, 0.01, 0]} />

        {/* Desk */}
        <mesh position={[0, 0.75, 0.6]} castShadow receiveShadow>
          <boxGeometry args={[2, 0.06, 0.9]} />
          <meshStandardMaterial color="#4a3728" roughness={0.6} />
        </mesh>
            
        {/* Laptop Base */}
<mesh position={[0.2, 0.82, 0.45]} castShadow>
  <boxGeometry args={[0.4, 0.02, 0.28]} />
  <meshStandardMaterial color="#1e293b" metalness={0.6} />
</mesh>

{/* Laptop Screen */}
<mesh position={[0.2, 0.97, 0.32]} rotation={[-0.25, 0, 0]}>
  <boxGeometry args={[0.4, 0.3, 0.015]} />
  <meshStandardMaterial color="#1e293b" metalness={0.6} />
</mesh>

{/* Screen Glow */}
<mesh position={[0.2, 0.97, 0.315]} rotation={[-0.25, 0, 0]}>
  <planeGeometry args={[0.36, 0.26]} />
  <meshBasicMaterial color="#3b82f6" />
</mesh>

{/* Plant Pot */}
<mesh position={[-4.5, 0.15, -2]}>
  <cylinderGeometry args={[0.15, 0.18, 0.3, 16]} />
  <meshStandardMaterial color="#4a3728" />
</mesh>

{/* Leaves */}
{[...Array(6)].map((_, i) => (
  <mesh
    key={i}
    position={[
      -4.5 + Math.cos(i) * 0.12,
      0.4 + i * 0.08,
      -2 + Math.sin(i) * 0.12
    ]}
  >
    <sphereGeometry args={[0.12, 8, 8]} />
    <meshStandardMaterial color="#1f4d2e" />
  </mesh>
))}
        {/* Avatar */}
        <Avatar mode="sitting" position={[0, 0, -0.2]} />
      </Canvas>
    </div>
  </React.StrictMode>
);