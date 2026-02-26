"use client";

import { useRef, useMemo, useCallback } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Float, Text } from "@react-three/drei";
import * as THREE from "three";

const TWITTER_BLUE = "#1DA1F2";
const AURORA_CYAN = "#06B6D4";
const AURORA_MAGENTA = "#D946EF";

/* ── Mouse-reactive tilt for the whole scene ── */
function MouseTilt({ children }: { children: React.ReactNode }) {
  const ref = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y += (state.pointer.x * 0.2 - ref.current.rotation.y) * 0.04;
      ref.current.rotation.x += (-state.pointer.y * 0.1 - ref.current.rotation.x) * 0.04;
    }
  });

  return <group ref={ref}>{children}</group>;
}

/* ── Notification bell: tweet notification ── */
function NotificationBubble({
  position,
  count,
  speed = 0.5,
}: {
  position: [number, number, number];
  count: string;
  speed?: number;
}) {
  const ref = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * speed) * 0.2;
      ref.current.rotation.z = Math.sin(state.clock.elapsedTime * speed * 0.8) * 0.1;
    }
  });

  return (
    <Float speed={speed * 2} rotationIntensity={0.15} floatIntensity={0.3}>
      <group ref={ref} position={position}>
        {/* Circle background */}
        <mesh>
          <circleGeometry args={[0.3, 32]} />
          <meshStandardMaterial
            color={TWITTER_BLUE}
            emissive={TWITTER_BLUE}
            emissiveIntensity={0.5}
            transparent
            opacity={0.2}
          />
        </mesh>
        {/* Ring */}
        <mesh>
          <ringGeometry args={[0.28, 0.32, 32]} />
          <meshBasicMaterial color={TWITTER_BLUE} transparent opacity={0.3} />
        </mesh>
        {/* Count text */}
        <Text
          position={[0, 0, 0.05]}
          fontSize={0.2}
          color={TWITTER_BLUE}
          anchorX="center"
          anchorY="middle"
          fillOpacity={0.4}
        >
          {count}
        </Text>
      </group>
    </Float>
  );
}

/* ── Floating hashtag tags ── */
function HashtagCloud({
  tags,
}: {
  tags: { text: string; position: [number, number, number]; size: number }[];
}) {
  return (
    <>
      {tags.map((tag) => (
        <Float key={tag.text} speed={0.6} rotationIntensity={0.1} floatIntensity={0.5}>
          <Text
            position={tag.position}
            fontSize={tag.size}
            color={AURORA_CYAN}
            anchorX="center"
            anchorY="middle"
            fillOpacity={0.12}
          >
            {tag.text}
          </Text>
        </Float>
      ))}
    </>
  );
}

/* ── Mouse-following ripple rings ── */
function MouseRipple() {
  const ring1 = useRef<THREE.Mesh>(null);
  const ring2 = useRef<THREE.Mesh>(null);
  const { pointer } = useThree();

  useFrame((state) => {
    const mx = pointer.x * 4;
    const my = pointer.y * 2.5;
    const pulse = Math.sin(state.clock.elapsedTime * 2) * 0.1 + 1;

    if (ring1.current) {
      ring1.current.position.x += (mx - ring1.current.position.x) * 0.03;
      ring1.current.position.y += (my - ring1.current.position.y) * 0.03;
      ring1.current.scale.setScalar(pulse);
    }
    if (ring2.current) {
      ring2.current.position.x += (mx - ring2.current.position.x) * 0.02;
      ring2.current.position.y += (my - ring2.current.position.y) * 0.02;
      ring2.current.scale.setScalar(pulse * 1.4);
    }
  });

  return (
    <>
      <mesh ref={ring1} position={[0, 0, -2]}>
        <ringGeometry args={[0.5, 0.55, 48]} />
        <meshBasicMaterial color={TWITTER_BLUE} transparent opacity={0.08} side={THREE.DoubleSide} />
      </mesh>
      <mesh ref={ring2} position={[0, 0, -3]}>
        <ringGeometry args={[0.8, 0.84, 48]} />
        <meshBasicMaterial color={AURORA_MAGENTA} transparent opacity={0.05} side={THREE.DoubleSide} />
      </mesh>
    </>
  );
}

/* ── Particle field ── */
function Particles({ count }: { count: number }) {
  const ref = useRef<THREE.Points>(null);
  const { pointer } = useThree();

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 16;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 8;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 8;
    }
    return pos;
  }, [count]);

  useFrame((state) => {
    if (!ref.current) return;
    ref.current.rotation.y = state.clock.elapsedTime * 0.015;
    // Subtle mouse influence on position
    ref.current.position.x += (pointer.x * 0.3 - ref.current.position.x) * 0.02;
    ref.current.position.y += (pointer.y * 0.15 - ref.current.position.y) * 0.02;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color={AURORA_MAGENTA} size={0.025} transparent opacity={0.45} sizeAttenuation />
    </points>
  );
}

/* ── Scene ── */
function OrbScene() {
  return (
    <>
      <ambientLight intensity={0.2} />
      <pointLight position={[3, 2, 4]} intensity={0.4} color={TWITTER_BLUE} />
      <pointLight position={[-3, -1, 3]} intensity={0.3} color={AURORA_MAGENTA} />

      <MouseTilt>
        {/* Notification bubbles */}
        <NotificationBubble position={[-3.5, 1, -2]} count="12" speed={0.6} />
        <NotificationBubble position={[3, -0.5, -3]} count="5" speed={0.45} />
        <NotificationBubble position={[0.5, 1.5, -4]} count="28" speed={0.5} />
        <NotificationBubble position={[-2, -1.2, -3]} count="3" speed={0.55} />

        {/* Hashtag cloud */}
        <HashtagCloud
          tags={[
            { text: "#leads", position: [-4, -0.5, -5], size: 0.35 },
            { text: "#outreach", position: [4, 1, -4], size: 0.3 },
            { text: "#AI", position: [-1, 2, -6], size: 0.4 },
            { text: "#growth", position: [2, -1.5, -5], size: 0.28 },
            { text: "#DM", position: [-3, 1.8, -4], size: 0.32 },
          ]}
        />

        {/* Orbital rings */}
        <Float speed={0.3} rotationIntensity={0.2} floatIntensity={0.3}>
          <mesh position={[0, 0, -4]} rotation={[0.5, 0, 0]}>
            <torusGeometry args={[2.5, 0.012, 16, 80]} />
            <meshBasicMaterial color={TWITTER_BLUE} transparent opacity={0.08} />
          </mesh>
        </Float>
        <Float speed={0.25} rotationIntensity={0.15} floatIntensity={0.2}>
          <mesh position={[0, 0, -4]} rotation={[0.8, 0.3, 0]}>
            <torusGeometry args={[3, 0.01, 16, 80]} />
            <meshBasicMaterial color={AURORA_CYAN} transparent opacity={0.06} />
          </mesh>
        </Float>
      </MouseTilt>

      <MouseRipple />
      <Particles count={200} />
    </>
  );
}

/* ── Canvas wrapper ── */
export function FloatingOrbs() {
  const onCreated = useCallback((state: { gl: THREE.WebGLRenderer }) => {
    state.gl.setClearColor(0x000000, 0);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden z-[1]" aria-hidden="true" style={{ pointerEvents: "auto" }}>
      <Canvas
        camera={{ position: [0, 0, 6], fov: 45 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
        onCreated={onCreated}
      >
        <OrbScene />
      </Canvas>
    </div>
  );
}
