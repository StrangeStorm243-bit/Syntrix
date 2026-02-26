import { useEffect, useState } from 'react';
import { Handle, Position } from '@xyflow/react';
import { BarChart3, Brain, Download, FileText, MessageCircle, Send } from 'lucide-react';
import type { PipelineStage } from './types';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const STAGE_ICONS: Record<string, any> = {
  collect: Download,
  judge: Brain,
  score: BarChart3,
  draft: FileText,
  send: Send,
  dm: MessageCircle,
};

function AnimatedCounter({ target }: { target: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (target === 0) {
      setDisplay(0);
      return;
    }
    const duration = 800;
    const steps = 30;
    const increment = target / steps;
    let current = 0;
    let step = 0;
    const timer = setInterval(() => {
      step++;
      current = Math.min(Math.round(increment * step), target);
      setDisplay(current);
      if (step >= steps) clearInterval(timer);
    }, duration / steps);
    return () => clearInterval(timer);
  }, [target]);

  return <>{display.toLocaleString()}</>;
}

export function StageNode({ data }: { data: PipelineStage & Record<string, unknown> }) {
  const Icon = STAGE_ICONS[data.id] ?? Download;

  const glowColor = data.color as string;
  const isActive = data.active as boolean;
  const count = data.count as number;
  const label = data.label as string;

  const borderStyle = isActive
    ? {
        borderColor: glowColor,
        boxShadow: `0 0 8px ${glowColor}80, 0 0 20px ${glowColor}40, inset 0 0 8px ${glowColor}10`,
      }
    : {
        borderColor: `${glowColor}40`,
        boxShadow: `0 0 4px ${glowColor}20`,
      };

  return (
    <div
      className="glass glass-hover"
      data-augmented-ui="tl-clip br-clip border"
      style={{
        width: 160,
        height: 120,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        padding: '12px 16px',
        borderRadius: 4,
        border: `1px solid`,
        cursor: 'default',
        position: 'relative',
        transition: 'box-shadow 0.3s ease, border-color 0.3s ease',
        ...borderStyle,
      }}
    >
      {/* Active pulse ring */}
      {isActive && (
        <div
          style={{
            position: 'absolute',
            inset: -2,
            borderRadius: 4,
            border: `1px solid ${glowColor}`,
            animation: 'ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite',
            opacity: 0.6,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Icon */}
      <div
        style={{
          color: glowColor,
          filter: isActive ? `drop-shadow(0 0 6px ${glowColor})` : 'none',
          transition: 'filter 0.3s ease',
        }}
      >
        <Icon size={20} strokeWidth={1.5} />
      </div>

      {/* Label */}
      <div
        style={{
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: 11,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: 'var(--cyber-text-dim)',
          lineHeight: 1,
        }}
      >
        {label}
      </div>

      {/* Count */}
      <div
        style={{
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: 22,
          fontWeight: 700,
          color: glowColor,
          lineHeight: 1,
          textShadow: isActive ? `0 0 10px ${glowColor}` : 'none',
          transition: 'text-shadow 0.3s ease',
        }}
      >
        <AnimatedCounter target={count} />
      </div>

      {/* Left handle (target) */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: glowColor,
          border: `2px solid ${glowColor}`,
          width: 8,
          height: 8,
          boxShadow: `0 0 6px ${glowColor}`,
          left: -4,
        }}
      />

      {/* Right handle (source) */}
      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: glowColor,
          border: `2px solid ${glowColor}`,
          width: 8,
          height: 8,
          boxShadow: `0 0 6px ${glowColor}`,
          right: -4,
        }}
      />

      <style>{`
        @keyframes ping {
          75%, 100% {
            transform: scale(1.08);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
}
