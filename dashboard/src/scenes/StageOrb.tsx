import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Text } from '@react-three/drei';
import type { MeshStandardMaterial } from 'three';

interface StageOrbProps {
  position: [number, number, number];
  color: string;
  label: string;
  count: number;
  active: boolean;
}

export function StageOrb({ position, color, label, count, active }: StageOrbProps) {
  const materialRef = useRef<MeshStandardMaterial>(null);

  useFrame(({ clock }) => {
    if (!active || !materialRef.current) return;
    const t = clock.getElapsedTime();
    materialRef.current.emissiveIntensity = 0.3 + 0.7 * (0.5 + 0.5 * Math.sin(t * 2.5));
  });

  return (
    <Float speed={2} floatIntensity={0.5}>
      <group position={position}>
        {/* Main icosahedron orb */}
        <mesh>
          <icosahedronGeometry args={[0.8, 1]} />
          <meshStandardMaterial
            ref={materialRef}
            color={color}
            emissive={color}
            emissiveIntensity={active ? 0.6 : 0.3}
            roughness={0.3}
            metalness={0.6}
          />
        </mesh>

        {/* Wireframe overlay — slightly larger */}
        <mesh scale={1.05}>
          <icosahedronGeometry args={[0.8, 1]} />
          <meshStandardMaterial
            color={color}
            wireframe
            transparent
            opacity={0.3}
          />
        </mesh>

        {/* Stage label */}
        <Text
          position={[0, 1.2, 0]}
          fontSize={0.3}
          color="white"
          anchorX="center"
          anchorY="middle"
        >
          {label}
        </Text>

        {/* Count display */}
        <Text
          position={[0, 0.8, 0]}
          fontSize={0.25}
          color="#a0a0b0"
          anchorX="center"
          anchorY="middle"
        >
          {String(count)}
        </Text>
      </group>
    </Float>
  );
}
