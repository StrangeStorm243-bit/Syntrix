import { useEffect, useState } from 'react';
import { cn } from '../../lib/utils';

interface FlipCardProps {
  frontSrc: string;
  backSrc: string;
  alt: string;
  className?: string;
  autoFlip?: boolean;
  autoFlipInterval?: number;
}

export function FlipCard({
  frontSrc,
  backSrc,
  alt,
  className,
  autoFlip = true,
  autoFlipInterval = 5000,
}: FlipCardProps) {
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    if (!autoFlip) return;
    const timer = setInterval(() => setFlipped((f) => !f), autoFlipInterval);
    return () => clearInterval(timer);
  }, [autoFlip, autoFlipInterval]);

  return (
    <div
      className={cn('group cursor-pointer', className)}
      style={{ perspective: '1200px' }}
      onClick={() => setFlipped((f) => !f)}
    >
      <div
        className="relative h-full w-full transition-transform duration-700"
        style={{
          transformStyle: 'preserve-3d',
          transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
        }}
      >
        {/* Front */}
        <div
          className="absolute inset-0 overflow-hidden rounded-lg"
          style={{ backfaceVisibility: 'hidden' }}
        >
          <img
            src={frontSrc}
            alt={`${alt} — before`}
            className="h-full w-full object-cover"
            loading="lazy"
          />
          <div
            className="absolute inset-0"
            style={{
              background:
                'linear-gradient(to bottom, transparent 60%, rgba(10, 6, 8, 0.8))',
            }}
          />
        </div>

        {/* Back */}
        <div
          className="absolute inset-0 overflow-hidden rounded-lg"
          style={{
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
          }}
        >
          <img
            src={backSrc}
            alt={`${alt} — after`}
            className="h-full w-full object-cover"
            loading="lazy"
          />
          <div
            className="absolute inset-0"
            style={{
              background:
                'linear-gradient(to bottom, transparent 60%, rgba(10, 6, 8, 0.8))',
            }}
          />
        </div>
      </div>
    </div>
  );
}
