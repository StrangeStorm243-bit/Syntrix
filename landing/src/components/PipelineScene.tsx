"use client";

import { useRef, useMemo, useCallback } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Float } from "@react-three/drei";
import * as THREE from "three";

const TWITTER_BLUE = "#1DA1F2";
const AURORA_CYAN = "#06B6D4";
const AURORA_MAGENTA = "#D946EF";
const AURORA_BLUE = "#3B82F6";

/* ── Data flow: animated particles traveling along paths ── */
function DataStream({
  start,
  end,
  color = TWITTER_BLUE,
  speed = 1,
  count = 8,
}: {
  start: [number, number, number];
  end: [number, number, number];
  color?: string;
  speed?: number;
  count?: number;
}) {
  const ref = useRef<THREE.Points>(null);

  const { positions, offsets } = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const off = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      off[i] = i / count;
      pos[i * 3] = start[0];
      pos[i * 3 + 1] = start[1];
      pos[i * 3 + 2] = start[2];
    }
    return { positions: pos, offsets: off };
  }, [count, start]);

  useFrame((state) => {
    if (!ref.current) return;
    const posArr = ref.current.geometry.attributes.position.array as Float32Array;
    const t = state.clock.elapsedTime * speed;

    for (let i = 0; i < count; i++) {
      const progress = (off[i] + t * 0.15) % 1;
      posArr[i * 3] = start[0] + (end[0] - start[0]) * progress;
      posArr[i * 3 + 1] = start[1] + (end[1] - start[1]) * progress + Math.sin(progress * Math.PI) * 0.15;
      posArr[i * 3 + 2] = start[2] + (end[2] - start[2]) * progress;
    }
    ref.current.geometry.attributes.position.needsUpdate = true;
  });

  const off = offsets;

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color={color} size={0.06} transparent opacity={0.7} sizeAttenuation />
    </points>
  );
}

/* ── Pipeline node: glowing sphere at each stage ── */
function PipelineNode({
  position,
  color,
  size = 0.2,
  pulseSpeed = 1,
}: {
  position: [number, number, number];
  color: string;
  size?: number;
  pulseSpeed?: number;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const pulse = Math.sin(state.clock.elapsedTime * pulseSpeed) * 0.15 + 1;
    if (glowRef.current) {
      glowRef.current.scale.setScalar(pulse);
    }
  });

  return (
    <group position={position}>
      {/* Core */}
      <mesh ref={ref}>
        <sphereGeometry args={[size, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.6}
          transparent
          opacity={0.4}
          metalness={0.5}
          roughness={0.3}
        />
      </mesh>
      {/* Glow ring */}
      <mesh ref={glowRef}>
        <ringGeometry args={[size * 1.3, size * 1.6, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.1} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

/* ── Mouse-reactive camera offset ── */
function MouseOffset({ children }: { children: React.ReactNode }) {
  const ref = useRef<THREE.Group>(null);
  const { pointer } = useThree();

  useFrame(() => {
    if (ref.current) {
      ref.current.position.x += (pointer.x * 0.5 - ref.current.position.x) * 0.03;
      ref.current.position.y += (pointer.y * 0.25 - ref.current.position.y) * 0.03;
    }
  });

  return <group ref={ref}>{children}</group>;
}

/* ── Static connection lines between nodes ── */
function PipelineEdges({ nodes }: { nodes: [number, number, number][] }) {
  const positions = useMemo(() => {
    const lines: number[] = [];
    for (let i = 0; i < nodes.length - 1; i++) {
      lines.push(...nodes[i], ...nodes[i + 1]);
    }
    return new Float32Array(lines);
  }, [nodes]);

  return (
    <lineSegments>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <lineBasicMaterial color={TWITTER_BLUE} transparent opacity={0.12} />
    </lineSegments>
  );
}

/* ── Ambient particles ── */
function AmbientParticles({ count }: { count: number }) {
  const ref = useRef<THREE.Points>(null);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 18;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 6;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 6;
    }
    return pos;
  }, [count]);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.01;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color={AURORA_BLUE} size={0.02} transparent opacity={0.35} sizeAttenuation />
    </points>
  );
}

/* ── Scene ── */
function Scene() {
  // 8 pipeline nodes spread horizontally
  const nodes: [number, number, number][] = [
    [-7, 0, -2],
    [-5, 0.5, -2],
    [-3, -0.3, -2],
    [-1, 0.2, -2],
    [1, -0.2, -2],
    [3, 0.4, -2],
    [5, -0.1, -2],
    [7, 0.3, -2],
  ];

  const colors = [
    AURORA_CYAN, AURORA_CYAN, AURORA_BLUE, AURORA_BLUE,
    AURORA_MAGENTA, AURORA_MAGENTA, AURORA_MAGENTA, AURORA_MAGENTA,
  ];

  return (
    <>
      <ambientLight intensity={0.2} />
      <pointLight position={[0, 3, 5]} intensity={0.4} color={TWITTER_BLUE} />
      <pointLight position={[-5, -2, 3]} intensity={0.2} color={AURORA_CYAN} />
      <pointLight position={[5, -2, 3]} intensity={0.2} color={AURORA_MAGENTA} />

      <MouseOffset>
        {/* Pipeline nodes */}
        {nodes.map((pos, i) => (
          <PipelineNode key={i} position={pos} color={colors[i]} size={0.18} pulseSpeed={0.8 + i * 0.1} />
        ))}

        {/* Edges */}
        <PipelineEdges nodes={nodes} />

        {/* Data streams flowing between nodes */}
        {nodes.slice(0, -1).map((start, i) => (
          <DataStream
            key={i}
            start={start}
            end={nodes[i + 1]}
            color={colors[i]}
            speed={0.8 + Math.random() * 0.4}
            count={6}
          />
        ))}

        {/* Decorative orbits */}
        <Float speed={0.3} rotationIntensity={0.1} floatIntensity={0.2}>
          <mesh position={[0, 0, -4]} rotation={[1.2, 0, 0]}>
            <torusGeometry args={[5, 0.008, 16, 100]} />
            <meshBasicMaterial color={TWITTER_BLUE} transparent opacity={0.06} />
          </mesh>
        </Float>
      </MouseOffset>

      <AmbientParticles count={120} />
    </>
  );
}

/* ── Canvas wrapper ── */
export function PipelineScene() {
  const onCreated = useCallback((state: { gl: THREE.WebGLRenderer }) => {
    state.gl.setClearColor(0x000000, 0);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden z-[1]" aria-hidden="true" style={{ pointerEvents: "auto" }}>
      <Canvas
        camera={{ position: [0, 0, 8], fov: 50 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
        onCreated={onCreated}
      >
        <Scene />
      </Canvas>
    </div>
  );
}
