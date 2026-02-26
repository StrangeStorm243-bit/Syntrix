"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial } from "@react-three/drei";
import type { Mesh, Group } from "three";

function FloatingShape({
  position,
  color,
  speed,
  distort,
  size,
  geometry,
}: {
  position: [number, number, number];
  color: string;
  speed: number;
  distort: number;
  size: number;
  geometry: "icosahedron" | "octahedron" | "torus" | "dodecahedron";
}) {
  const meshRef = useRef<Mesh>(null);

  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * speed * 0.3;
      meshRef.current.rotation.y += delta * speed * 0.2;
    }
  });

  const geo = useMemo(() => {
    switch (geometry) {
      case "icosahedron":
        return <icosahedronGeometry args={[size, 1]} />;
      case "octahedron":
        return <octahedronGeometry args={[size, 0]} />;
      case "torus":
        return <torusGeometry args={[size, size * 0.35, 16, 32]} />;
      case "dodecahedron":
        return <dodecahedronGeometry args={[size, 0]} />;
    }
  }, [geometry, size]);

  return (
    <Float speed={speed * 0.8} rotationIntensity={0.4} floatIntensity={0.6}>
      <mesh ref={meshRef} position={position}>
        {geo}
        <MeshDistortMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.3}
          transparent
          opacity={0.15}
          wireframe
          distort={distort}
          speed={speed}
        />
      </mesh>
    </Float>
  );
}

function Particles({ count }: { count: number }) {
  const groupRef = useRef<Group>(null);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 20;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 14;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    return pos;
  }, [count]);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.015;
    }
  });

  return (
    <group ref={groupRef}>
      <points>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[positions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          color="#06B6D4"
          size={0.03}
          transparent
          opacity={0.6}
          sizeAttenuation
        />
      </points>
    </group>
  );
}

function Scene() {
  return (
    <>
      <ambientLight intensity={0.2} />
      <pointLight position={[5, 5, 5]} intensity={0.5} color="#06B6D4" />
      <pointLight position={[-5, -3, 3]} intensity={0.3} color="#D946EF" />

      {/* Large floating shapes */}
      <FloatingShape
        position={[-4.5, 1.5, -3]}
        color="#06B6D4"
        speed={0.6}
        distort={0.3}
        size={1.8}
        geometry="icosahedron"
      />
      <FloatingShape
        position={[4.5, -1, -2]}
        color="#D946EF"
        speed={0.4}
        distort={0.25}
        size={1.4}
        geometry="torus"
      />
      <FloatingShape
        position={[-2, -2.5, -4]}
        color="#3B82F6"
        speed={0.5}
        distort={0.2}
        size={1.2}
        geometry="octahedron"
      />
      <FloatingShape
        position={[3, 2.5, -5]}
        color="#06B6D4"
        speed={0.35}
        distort={0.15}
        size={1.0}
        geometry="dodecahedron"
      />
      <FloatingShape
        position={[0, -3, -3]}
        color="#D946EF"
        speed={0.45}
        distort={0.2}
        size={0.8}
        geometry="icosahedron"
      />

      <Particles count={300} />
    </>
  );
}

export function HeroScene() {
  return (
    <div className="pointer-events-none absolute inset-0" aria-hidden="true">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 50 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <Scene />
      </Canvas>
    </div>
  );
}
