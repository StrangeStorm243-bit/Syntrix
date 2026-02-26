"use client";

import { useRef, useMemo, useCallback } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Float, Text, MeshDistortMaterial } from "@react-three/drei";
import * as THREE from "three";

const TWITTER_BLUE = "#1DA1F2";
const TWITTER_DARK = "#14171A";
const TWITTER_LIGHT = "#AAB8C2";
const AURORA_CYAN = "#06B6D4";
const AURORA_MAGENTA = "#D946EF";

/* ── Mouse-reactive group: whole scene tilts toward cursor ── */
function MouseParallax({ children }: { children: React.ReactNode }) {
  const groupRef = useRef<THREE.Group>(null);
  const target = useRef({ x: 0, y: 0 });

  useFrame((state) => {
    target.current.x = state.pointer.x * 0.3;
    target.current.y = state.pointer.y * 0.15;
    if (groupRef.current) {
      groupRef.current.rotation.y += (target.current.x - groupRef.current.rotation.y) * 0.05;
      groupRef.current.rotation.x += (-target.current.y - groupRef.current.rotation.x) * 0.05;
    }
  });

  return <group ref={groupRef}>{children}</group>;
}

/* ── Bird silhouette: a stylised shape extruded into 3D ── */
function BirdShape({
  position,
  scale = 1,
  color = TWITTER_BLUE,
  speed = 0.5,
}: {
  position: [number, number, number];
  scale?: number;
  color?: string;
  speed?: number;
}) {
  const meshRef = useRef<THREE.Mesh>(null);

  const geometry = useMemo(() => {
    const shape = new THREE.Shape();
    // Simplified bird / twitter-like silhouette
    shape.moveTo(0, 0);
    shape.bezierCurveTo(0.1, 0.4, 0.5, 0.7, 0.9, 0.5);
    shape.bezierCurveTo(1.1, 0.4, 1.0, 0.6, 1.3, 0.8);
    shape.bezierCurveTo(1.0, 0.7, 0.8, 0.8, 0.6, 0.9);
    shape.bezierCurveTo(0.9, 1.0, 1.2, 1.2, 1.5, 1.0);
    shape.bezierCurveTo(1.1, 1.2, 0.7, 1.1, 0.5, 0.9);
    shape.bezierCurveTo(0.2, 1.1, -0.2, 1.0, -0.3, 0.7);
    shape.bezierCurveTo(-0.2, 0.4, -0.1, 0.2, 0, 0);
    const extrudeSettings = { depth: 0.08, bevelEnabled: true, bevelThickness: 0.02, bevelSize: 0.02, bevelSegments: 3 };
    return new THREE.ExtrudeGeometry(shape, extrudeSettings);
  }, []);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * speed) * 0.3;
      meshRef.current.rotation.z = Math.sin(state.clock.elapsedTime * speed * 0.7) * 0.15;
    }
  });

  return (
    <Float speed={speed * 2} rotationIntensity={0.2} floatIntensity={0.4}>
      <mesh ref={meshRef} position={position} scale={scale} geometry={geometry}>
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.4}
          transparent
          opacity={0.25}
          metalness={0.6}
          roughness={0.3}
        />
      </mesh>
    </Float>
  );
}

/* ── Floating tweet card: a rounded rect with glow ── */
function TweetCard({
  position,
  rotation,
  width = 1.6,
  height = 0.9,
  speed = 0.4,
}: {
  position: [number, number, number];
  rotation?: [number, number, number];
  width?: number;
  height?: number;
  speed?: number;
}) {
  const meshRef = useRef<THREE.Mesh>(null);

  const geometry = useMemo(() => {
    const shape = new THREE.Shape();
    const r = 0.08;
    shape.moveTo(r, 0);
    shape.lineTo(width - r, 0);
    shape.quadraticCurveTo(width, 0, width, r);
    shape.lineTo(width, height - r);
    shape.quadraticCurveTo(width, height, width - r, height);
    shape.lineTo(r, height);
    shape.quadraticCurveTo(0, height, 0, height - r);
    shape.lineTo(0, r);
    shape.quadraticCurveTo(0, 0, r, 0);
    return new THREE.ShapeGeometry(shape);
  }, [width, height]);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * speed + position[0]) * 0.15;
    }
  });

  return (
    <Float speed={speed * 1.5} rotationIntensity={0.1} floatIntensity={0.3}>
      <mesh
        ref={meshRef}
        position={position}
        rotation={rotation ?? [0, 0, 0]}
        geometry={geometry}
      >
        <meshStandardMaterial
          color={TWITTER_DARK}
          emissive={TWITTER_BLUE}
          emissiveIntensity={0.15}
          transparent
          opacity={0.12}
          side={THREE.DoubleSide}
          metalness={0.3}
          roughness={0.7}
        />
      </mesh>
      {/* Border glow */}
      <mesh position={position} rotation={rotation ?? [0, 0, 0]} geometry={geometry}>
        <meshBasicMaterial
          color={TWITTER_BLUE}
          transparent
          opacity={0.06}
          wireframe
          side={THREE.DoubleSide}
        />
      </mesh>
    </Float>
  );
}

/* ── Floating @ and # symbols ── */
function TwitterSymbol({
  text,
  position,
  color = TWITTER_BLUE,
  size = 0.6,
  speed = 0.3,
}: {
  text: string;
  position: [number, number, number];
  color?: string;
  size?: number;
  speed?: number;
}) {
  const ref = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * speed + position[0] * 2) * 0.2;
      ref.current.rotation.y = Math.sin(state.clock.elapsedTime * speed * 0.5) * 0.3;
    }
  });

  return (
    <group ref={ref} position={position}>
      <Text
        fontSize={size}
        color={color}
        anchorX="center"
        anchorY="middle"
        fillOpacity={0.18}
      >
        {text}
        <meshBasicMaterial color={color} transparent opacity={0.18} />
      </Text>
    </group>
  );
}

/* ── Mouse-following particle swarm ── */
function TwitterParticles({ count }: { count: number }) {
  const ref = useRef<THREE.Points>(null);
  const { pointer } = useThree();

  const { positions, velocities } = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 20;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 14;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 10;
      vel[i * 3] = (Math.random() - 0.5) * 0.002;
      vel[i * 3 + 1] = (Math.random() - 0.5) * 0.002;
      vel[i * 3 + 2] = (Math.random() - 0.5) * 0.001;
    }
    return { positions: pos, velocities: vel };
  }, [count]);

  useFrame(() => {
    if (!ref.current) return;
    const posAttr = ref.current.geometry.attributes.position;
    const arr = posAttr.array as Float32Array;
    const mx = pointer.x * 5;
    const my = pointer.y * 3;

    for (let i = 0; i < count; i++) {
      const ix = i * 3;
      // Drift
      arr[ix] += velocities[ix];
      arr[ix + 1] += velocities[ix + 1];
      arr[ix + 2] += velocities[ix + 2];
      // Gentle pull toward mouse
      arr[ix] += (mx - arr[ix]) * 0.0003;
      arr[ix + 1] += (my - arr[ix + 1]) * 0.0003;
      // Wrap around
      if (arr[ix] > 10) arr[ix] = -10;
      if (arr[ix] < -10) arr[ix] = 10;
      if (arr[ix + 1] > 7) arr[ix + 1] = -7;
      if (arr[ix + 1] < -7) arr[ix + 1] = 7;
    }
    posAttr.needsUpdate = true;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        color={TWITTER_BLUE}
        size={0.035}
        transparent
        opacity={0.55}
        sizeAttenuation
      />
    </points>
  );
}

/* ── Connection lines: network graph between nodes ── */
function ConnectionLines() {
  const ref = useRef<THREE.LineSegments>(null);

  const positions = useMemo(() => {
    const nodes = [
      [-4, 1.5, -3], [4, -0.5, -2], [-2, -2, -4],
      [3, 2, -5], [0, -3, -3], [-3, 3, -4],
      [5, 1, -4], [-1, 1, -2], [2, -2, -3],
    ];
    const lines: number[] = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i][0] - nodes[j][0];
        const dy = nodes[i][1] - nodes[j][1];
        const dz = nodes[i][2] - nodes[j][2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < 5.5) {
          lines.push(...nodes[i], ...nodes[j]);
        }
      }
    }
    return new Float32Array(lines);
  }, []);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.05) * 0.1;
    }
  });

  return (
    <lineSegments ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <lineBasicMaterial color={TWITTER_BLUE} transparent opacity={0.06} />
    </lineSegments>
  );
}

/* ── Wireframe globe: represents the network ── */
function WireframeGlobe({ position, size = 2 }: { position: [number, number, number]; size?: number }) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.08;
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.03) * 0.1;
    }
  });

  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[size, 24, 24]} />
      <meshBasicMaterial color={TWITTER_BLUE} wireframe transparent opacity={0.04} />
    </mesh>
  );
}

/* ── Main scene ── */
function Scene() {
  return (
    <>
      <ambientLight intensity={0.25} />
      <pointLight position={[5, 5, 5]} intensity={0.5} color={TWITTER_BLUE} />
      <pointLight position={[-5, -3, 3]} intensity={0.3} color={AURORA_MAGENTA} />
      <pointLight position={[0, 3, 4]} intensity={0.2} color={AURORA_CYAN} />

      <MouseParallax>
        {/* Birds */}
        <BirdShape position={[-4.5, 2, -3]} scale={0.7} color={TWITTER_BLUE} speed={0.6} />
        <BirdShape position={[4, -1, -4]} scale={0.5} color={AURORA_CYAN} speed={0.45} />
        <BirdShape position={[-2, -2.5, -5]} scale={0.4} color={TWITTER_BLUE} speed={0.55} />
        <BirdShape position={[2.5, 3, -6]} scale={0.35} color={TWITTER_LIGHT} speed={0.35} />

        {/* Tweet cards */}
        <TweetCard position={[-3.5, -0.5, -2]} rotation={[0, 0.3, 0.05]} speed={0.4} />
        <TweetCard position={[3, 1.5, -3]} rotation={[0, -0.2, -0.03]} width={1.4} height={0.8} speed={0.35} />
        <TweetCard position={[0.5, -2, -4]} rotation={[0.1, 0.15, 0]} width={1.2} height={0.7} speed={0.5} />
        <TweetCard position={[-1.5, 2.5, -5]} rotation={[0, -0.1, 0.05]} width={1.8} height={1.0} speed={0.3} />

        {/* Symbols */}
        <TwitterSymbol text="@" position={[-5, 0.5, -4]} color={TWITTER_BLUE} size={0.9} speed={0.3} />
        <TwitterSymbol text="#" position={[5, -1.5, -5]} color={AURORA_CYAN} size={0.8} speed={0.25} />
        <TwitterSymbol text="DM" position={[1, 3.5, -6]} color={AURORA_MAGENTA} size={0.5} speed={0.35} />
        <TwitterSymbol text="RT" position={[-3, -3, -5]} color={TWITTER_BLUE} size={0.45} speed={0.4} />
        <TwitterSymbol text="X" position={[4.5, 2.5, -7]} color={TWITTER_LIGHT} size={1.1} speed={0.2} />

        {/* Wireframe globe */}
        <WireframeGlobe position={[0, 0, -8]} size={4} />

        {/* Network lines */}
        <ConnectionLines />

        {/* Floating geometric accents */}
        <Float speed={0.6} rotationIntensity={0.5} floatIntensity={0.6}>
          <mesh position={[-6, -1, -6]}>
            <octahedronGeometry args={[0.6, 0]} />
            <MeshDistortMaterial
              color={TWITTER_BLUE}
              emissive={TWITTER_BLUE}
              emissiveIntensity={0.3}
              transparent
              opacity={0.12}
              wireframe
              distort={0.2}
              speed={0.5}
            />
          </mesh>
        </Float>
        <Float speed={0.4} rotationIntensity={0.3} floatIntensity={0.5}>
          <mesh position={[6, 1.5, -5]}>
            <icosahedronGeometry args={[0.8, 1]} />
            <MeshDistortMaterial
              color={AURORA_CYAN}
              emissive={AURORA_CYAN}
              emissiveIntensity={0.3}
              transparent
              opacity={0.1}
              wireframe
              distort={0.15}
              speed={0.4}
            />
          </mesh>
        </Float>
      </MouseParallax>

      {/* Particles (outside parallax for independent motion) */}
      <TwitterParticles count={400} />
    </>
  );
}

/* ── Canvas wrapper ── */
export function HeroScene() {
  const onCreated = useCallback((state: { gl: THREE.WebGLRenderer }) => {
    state.gl.setClearColor(0x000000, 0);
  }, []);

  return (
    <div className="absolute inset-0 z-[1]" aria-hidden="true" style={{ pointerEvents: "auto" }}>
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
