"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float } from "@react-three/drei";
import type { Mesh, Points } from "three";

function Orb({
  position,
  color,
  size,
  speed,
}: {
  position: [number, number, number];
  color: string;
  size: number;
  speed: number;
}) {
  const ref = useRef<Mesh>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * speed * 0.5;
      ref.current.rotation.z = Math.sin(state.clock.elapsedTime * speed * 0.3) * 0.3;
    }
  });

  return (
    <Float speed={speed} rotationIntensity={0.3} floatIntensity={0.8}>
      <mesh ref={ref} position={position}>
        <sphereGeometry args={[size, 32, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.5}
          transparent
          opacity={0.12}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>
      {/* Wireframe ring */}
      <mesh position={position} rotation={[Math.PI / 3, 0, 0]}>
        <torusGeometry args={[size * 1.6, 0.015, 16, 64]} />
        <meshBasicMaterial color={color} transparent opacity={0.2} />
      </mesh>
    </Float>
  );
}

function DriftingParticles({ count }: { count: number }) {
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 16;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 6;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 8;
    }
    return pos;
  }, [count]);

  const ref = useRef<Points>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.01;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        color="#D946EF"
        size={0.02}
        transparent
        opacity={0.5}
        sizeAttenuation
      />
    </points>
  );
}

function OrbScene() {
  return (
    <>
      <ambientLight intensity={0.15} />
      <pointLight position={[3, 2, 4]} intensity={0.4} color="#D946EF" />
      <pointLight position={[-3, -1, 3]} intensity={0.3} color="#06B6D4" />

      <Orb position={[-3.5, 0.5, -2]} color="#06B6D4" size={0.6} speed={0.8} />
      <Orb position={[3.5, -0.3, -3]} color="#D946EF" size={0.5} speed={0.6} />
      <Orb position={[0.5, 0.8, -4]} color="#3B82F6" size={0.4} speed={0.7} />

      <DriftingParticles count={150} />
    </>
  );
}

export function FloatingOrbs() {
  return (
    <div
      className="pointer-events-none absolute inset-0 overflow-hidden"
      aria-hidden="true"
    >
      <Canvas
        camera={{ position: [0, 0, 6], fov: 45 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <OrbScene />
      </Canvas>
    </div>
  );
}
