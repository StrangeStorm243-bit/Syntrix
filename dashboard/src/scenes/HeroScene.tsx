import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { AdaptiveDpr, Float, Sparkles } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import type { Mesh } from 'three';

interface HeroSceneProps {
  gpuTier: 'high' | 'medium' | 'low';
}

function HeroContent({ gpuTier }: { gpuTier: 'high' | 'medium' }) {
  const meshRef = useRef<Mesh>(null);

  useFrame((_state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.15;
    }
  });

  return (
    <>
      <fog attach="fog" args={['#0a0608', 4, 15]} />
      <ambientLight intensity={0.15} />
      <directionalLight color="#ff6688" intensity={0.5} position={[5, 5, 5]} />
      <Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.5}>
        <mesh ref={meshRef}>
          <icosahedronGeometry args={[2, 1]} />
          <meshStandardMaterial
            wireframe
            color="#ff1493"
            emissive="#ff1493"
            emissiveIntensity={0.4}
          />
        </mesh>
      </Float>
      <Sparkles count={50} scale={6} size={2} speed={0.3} color="#ff6b35" />
      {gpuTier === 'high' && (
        <EffectComposer>
          <Bloom luminanceThreshold={0.6} intensity={1.5} levels={5} mipmapBlur />
        </EffectComposer>
      )}
    </>
  );
}

export default function HeroScene({ gpuTier }: HeroSceneProps) {
  if (gpuTier === 'low') {
    return (
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(ellipse at 50% 50%, rgba(255,20,147,0.08) 0%, transparent 70%)',
        }}
      />
    );
  }

  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 60 }}
      style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
    >
      <AdaptiveDpr pixelated />
      <HeroContent gpuTier={gpuTier} />
    </Canvas>
  );
}
