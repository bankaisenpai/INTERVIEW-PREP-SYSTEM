import React from "react";
import ReactDOM from "react-dom/client";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF, useAnimations } from "@react-three/drei";
import { useEffect, useRef } from "react";
import * as THREE from "three";

function Avatar({ mode }) {
  const group = useRef();

  const { scene } = useGLTF("/character.glb");

  const sitting = useGLTF("/animations/Sitting.glb");
  const talking = useGLTF("/animations/Talking.glb");

  const animations = [
    ...sitting.animations,
    ...talking.animations,
  ];

  const { actions } = useAnimations(animations, group);

  useEffect(() => {
    if (!actions) return;

    Object.values(actions).forEach((action) => action.stop());

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
      scale={1.8}
      position={[0, -1, 0]}
    />
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Canvas camera={{ position: [0, 1.5, 3], fov: 40 }}>
      <ambientLight intensity={1.5} />
      <directionalLight position={[2, 5, 2]} intensity={2} />
      <Avatar mode="sitting" />
      <OrbitControls enableZoom={false} />
    </Canvas>
  </React.StrictMode>
);