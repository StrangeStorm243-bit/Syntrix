import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import type { PipelineFlowData } from '../pipeline/types';
import { StageOrb } from './StageOrb';
import { PipelineParticles } from './PipelineParticles';

interface PipelineSceneProps {
  data: PipelineFlowData;
}

function computeStagePositions(
  stages: PipelineFlowData['stages']
): Map<string, [number, number, number]> {
  const posMap = new Map<string, [number, number, number]>();
  const count = stages.length;

  if (count === 0) return posMap;

  stages.forEach((stage, index) => {
    // Spread from x=-6 to x=6 in a horizontal arc
    const x = count === 1 ? 0 : -6 + (12 / (count - 1)) * index;
    const y = 0;
    const z = 0;
    posMap.set(stage.id, [x, y, z]);
  });

  return posMap;
}

function SceneContent({ data }: PipelineSceneProps) {
  const { stages, edges } = data;

  const stagePositions = computeStagePositions(stages);

  const particleEdges = edges
    .map((edge) => {
      const sourcePos = stagePositions.get(edge.source);
      const targetPos = stagePositions.get(edge.target);
      if (!sourcePos || !targetPos) return null;
      return {
        sourcePos,
        targetPos,
        throughput: edge.throughput,
        color: '#ff1493',
      };
    })
    .filter(
      (
        e
      ): e is {
        sourcePos: [number, number, number];
        targetPos: [number, number, number];
        throughput: number;
        color: string;
      } => e !== null
    );

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.2} />
      <pointLight position={[5, 5, 5]} intensity={1.5} />

      {/* Stage orbs */}
      {stages.map((stage) => {
        const pos = stagePositions.get(stage.id) ?? [0, 0, 0];
        return (
          <StageOrb
            key={stage.id}
            position={pos}
            color={stage.color}
            label={stage.label}
            count={stage.count}
            active={stage.active}
          />
        );
      })}

      {/* Data flow particles */}
      <PipelineParticles edges={particleEdges} />

      {/* Post-processing */}
      <EffectComposer>
        <Bloom luminanceThreshold={0.5} intensity={1.2} levels={5} mipmapBlur />
      </EffectComposer>

      {/* Camera controls */}
      <OrbitControls
        enableZoom
        enablePan
        autoRotate={false}
        maxPolarAngle={Math.PI / 2}
      />
    </>
  );
}

export default function PipelineScene({ data }: PipelineSceneProps) {
  return (
    <Canvas
      camera={{ position: [0, 2, 12], fov: 60 }}
      style={{ background: '#0a0608' }}
    >
      <SceneContent data={data} />
    </Canvas>
  );
}
