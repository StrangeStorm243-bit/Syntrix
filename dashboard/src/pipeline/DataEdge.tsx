import { useId } from 'react';
import { BaseEdge, getBezierPath, type EdgeProps } from '@xyflow/react';

const PARTICLE_COLOR = '#ff1493';
const BASE_DURATION = 3; // seconds at throughput=0
const MIN_DURATION = 0.8; // seconds at high throughput

function particleDuration(throughput: number): number {
  // More flow = faster particle (lower duration)
  const clamped = Math.max(0, Math.min(throughput, 100));
  const t = clamped / 100;
  return BASE_DURATION - t * (BASE_DURATION - MIN_DURATION);
}

function particleCount(throughput: number): number {
  if (throughput > 10) return 3;
  if (throughput > 0) return 2;
  return 1;
}

interface ParticleProps {
  pathId: string;
  filterId: string;
  duration: number;
  delay: number;
}

function Particle({ pathId, filterId, duration, delay }: ParticleProps) {
  return (
    <circle r={3} fill={PARTICLE_COLOR} filter={`url(#${filterId})`}>
      <animateMotion
        dur={`${duration}s`}
        begin={`${delay}s`}
        repeatCount="indefinite"
        rotate="auto"
      >
        <mpath href={`#${pathId}`} />
      </animateMotion>
    </circle>
  );
}

export function DataEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: EdgeProps) {
  const uid = useId().replace(/:/g, '');
  const pathId = `path-${uid}-${id}`;
  const filterId = `glow-${uid}-${id}`;

  const throughput = typeof data?.throughput === 'number' ? data.throughput : 0;

  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const duration = particleDuration(throughput);
  const count = particleCount(throughput);

  return (
    <>
      <defs>
        <filter id={filterId} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        {/* Named path for animateMotion mpath reference */}
        <path id={pathId} d={edgePath} />
      </defs>

      {/* Base edge path — rendered via BaseEdge for proper xyflow integration */}
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: 'rgba(255, 20, 147, 0.3)',
          strokeWidth: 1.5,
        }}
      />

      {/* Animated particles */}
      {Array.from({ length: count }, (_, i) => (
        <Particle
          key={i}
          pathId={pathId}
          filterId={filterId}
          duration={duration}
          delay={(duration / count) * i}
        />
      ))}
    </>
  );
}
