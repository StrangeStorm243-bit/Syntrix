import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface EdgeConfig {
  sourcePos: [number, number, number];
  targetPos: [number, number, number];
  throughput: number;
  color: string;
}

interface PipelineParticlesProps {
  edges: EdgeConfig[];
}

const PARTICLE_COLOR = '#ff1493';
const MAX_PARTICLES = 200;

interface ParticleData {
  sourcePos: THREE.Vector3;
  targetPos: THREE.Vector3;
  progress: number;
  speed: number;
}

export function PipelineParticles({ edges }: PipelineParticlesProps) {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const dummyRef = useRef(new THREE.Object3D());

  const { particles, totalCount } = useMemo(() => {
    if (edges.length === 0) return { particles: [] as ParticleData[], totalCount: 0 };

    const result: ParticleData[] = [];

    for (const edge of edges) {
      const count = Math.min(Math.ceil(edge.throughput / 5), MAX_PARTICLES - result.length);
      if (count <= 0) break;

      for (let i = 0; i < count; i++) {
        result.push({
          sourcePos: new THREE.Vector3(...edge.sourcePos),
          targetPos: new THREE.Vector3(...edge.targetPos),
          progress: Math.random(), // stagger initial positions
          speed: 0.003 + Math.random() * 0.003,
        });

        if (result.length >= MAX_PARTICLES) break;
      }

      if (result.length >= MAX_PARTICLES) break;
    }

    return { particles: result, totalCount: result.length };
  }, [edges]);

  const particleProgressRef = useRef<Float32Array>(
    new Float32Array(MAX_PARTICLES).map(() => Math.random())
  );

  useFrame(() => {
    const mesh = meshRef.current;
    if (!mesh || totalCount === 0) return;

    const dummy = dummyRef.current;
    const progress = particleProgressRef.current;
    const arcHeight = 1.5;

    for (let i = 0; i < totalCount; i++) {
      const p = particles[i];
      progress[i] += p.speed;
      if (progress[i] >= 1) {
        progress[i] = 0;
      }

      const t = progress[i];

      // Quadratic bezier: P(t) = (1-t)^2 * P0 + 2(1-t)t * Pmid + t^2 * P1
      const midX = (p.sourcePos.x + p.targetPos.x) * 0.5;
      const midY = Math.max(p.sourcePos.y, p.targetPos.y) + arcHeight;
      const midZ = (p.sourcePos.z + p.targetPos.z) * 0.5;

      const inv = 1 - t;
      const x = inv * inv * p.sourcePos.x + 2 * inv * t * midX + t * t * p.targetPos.x;
      const y = inv * inv * p.sourcePos.y + 2 * inv * t * midY + t * t * p.targetPos.y;
      const z = inv * inv * p.sourcePos.z + 2 * inv * t * midZ + t * t * p.targetPos.z;

      dummy.position.set(x, y, z);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    }

    mesh.instanceMatrix.needsUpdate = true;
  });

  if (totalCount === 0) return null;

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, totalCount]}>
      <sphereGeometry args={[0.05, 6, 6]} />
      <meshBasicMaterial
        color={PARTICLE_COLOR}
        transparent
        opacity={0.8}
      />
    </instancedMesh>
  );
}
