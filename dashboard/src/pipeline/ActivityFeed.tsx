import { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import type { PipelineEvent } from './types';

const STAGE_COLORS: Record<string, string> = {
  collect: '#ff1493',
  judge: '#ff6b35',
  score: '#ffd700',
  draft: '#ff1493',
  send: '#ff6b35',
};

const EVENT_TYPE_COLORS: Record<string, string> = {
  item_entered: '#ffd700',
  item_completed: '#00ff88',
  item_failed: '#ff4444',
};

function formatTimestamp(ts: number): string {
  const d = new Date(ts);
  const hh = d.getHours().toString().padStart(2, '0');
  const mm = d.getMinutes().toString().padStart(2, '0');
  const ss = d.getSeconds().toString().padStart(2, '0');
  return `${hh}:${mm}:${ss}`;
}

interface EventRowProps {
  event: PipelineEvent;
}

function EventRow({ event }: EventRowProps) {
  const stageColor = STAGE_COLORS[event.stage] ?? '#ff1493';
  const typeColor = EVENT_TYPE_COLORS[event.type] ?? '#ffd700';

  const typeLabel =
    event.type === 'item_entered'
      ? 'IN'
      : event.type === 'item_completed'
        ? 'OK'
        : 'ERR';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '5px 10px',
        borderBottom: '1px solid rgba(255, 20, 147, 0.06)',
        fontFamily: 'var(--font-mono, monospace)',
        fontSize: 11,
      }}
    >
      {/* Timestamp */}
      <span style={{ color: 'var(--cyber-text-dim)', flexShrink: 0, minWidth: 54 }}>
        {formatTimestamp(event.timestamp)}
      </span>

      {/* Stage badge */}
      <span
        style={{
          color: stageColor,
          border: `1px solid ${stageColor}50`,
          borderRadius: 2,
          padding: '1px 5px',
          fontSize: 10,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          flexShrink: 0,
          minWidth: 44,
          textAlign: 'center',
          background: `${stageColor}10`,
        }}
      >
        {event.stage}
      </span>

      {/* Type indicator */}
      <span
        style={{
          color: typeColor,
          fontWeight: 700,
          fontSize: 10,
          flexShrink: 0,
          minWidth: 24,
        }}
      >
        {typeLabel}
      </span>

      {/* Detail text */}
      <span
        style={{
          color: 'var(--cyber-text)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          flex: 1,
          opacity: 0.8,
        }}
      >
        {event.detail}
      </span>
    </motion.div>
  );
}

interface ActivityFeedProps {
  events: PipelineEvent[];
  isLive: boolean;
}

export function ActivityFeed({ events, isLive }: ActivityFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to top when new events arrive (newest at top)
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [events.length]);

  return (
    <div
      className="glass"
      style={{
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 4,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 12px',
          borderBottom: '1px solid rgba(255, 20, 147, 0.15)',
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-mono, monospace)',
            fontSize: 11,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: 'var(--cyber-text)',
            fontWeight: 600,
          }}
        >
          Activity Feed
        </span>

        {/* LIVE indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div
            style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: isLive ? '#00ff88' : '#555',
              boxShadow: isLive ? '0 0 6px #00ff88' : 'none',
              animation: isLive ? 'livePulse 1.5s ease-in-out infinite' : 'none',
            }}
          />
          <span
            style={{
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: 10,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: isLive ? '#00ff88' : '#555',
              fontWeight: 600,
            }}
          >
            {isLive ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
      </div>

      {/* Event list */}
      <div
        ref={scrollRef}
        style={{
          height: 320, // h-80
          overflowY: 'auto',
          scrollbarWidth: 'thin',
          scrollbarColor: 'rgba(255,20,147,0.3) transparent',
        }}
      >
        {events.length === 0 ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: 'var(--cyber-text-dim)',
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: 11,
              letterSpacing: '0.08em',
            }}
          >
            NO EVENTS YET
          </div>
        ) : (
          <AnimatePresence initial={false} mode="popLayout">
            {events.map((event) => (
              <EventRow key={event.id} event={event} />
            ))}
          </AnimatePresence>
        )}
      </div>

      <style>{`
        @keyframes livePulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
