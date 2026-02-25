import { useCallback, useEffect, useState } from 'react';
import Particles, { initParticlesEngine } from '@tsparticles/react';
import type { ISourceOptions } from '@tsparticles/engine';
import { loadSlim } from '@tsparticles/slim';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { usePerformanceMode } from '../../hooks/usePerformanceMode';

function getParticleCount(): number {
  const width = window.innerWidth;
  if (width >= 1024) return 100;
  if (width >= 768) return 50;
  return 30;
}

export function ParticleBackground() {
  const [engineReady, setEngineReady] = useState(false);
  const prefersReducedMotion = useReducedMotion();
  const { performanceMode } = usePerformanceMode();

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => {
      setEngineReady(true);
    });
  }, []);

  const particlesLoaded = useCallback(async () => {
    // no-op: container available here if needed in the future
  }, []);

  const fullOptions: ISourceOptions = {
    background: {
      color: {
        value: 'transparent',
      },
    },
    fpsLimit: 60,
    particles: {
      number: {
        value: getParticleCount(),
        density: {
          enable: false,
        },
      },
      color: {
        value: '#ff1493',
      },
      shape: {
        type: 'circle',
      },
      opacity: {
        value: 0.3,
      },
      size: {
        value: { min: 1, max: 3 },
      },
      links: {
        enable: true,
        distance: 150,
        color: '#ff1493',
        opacity: 0.1,
        width: 1,
      },
      move: {
        enable: true,
        speed: 0.3,
        direction: 'top',
        random: true,
        straight: false,
        outModes: {
          default: 'out',
        },
      },
    },
    interactivity: {
      events: {
        onHover: {
          enable: true,
          mode: 'repulse',
        },
      },
      modes: {
        repulse: {
          distance: 100,
          duration: 0.4,
        },
      },
    },
    detectRetina: true,
  };

  const reducedOptions: ISourceOptions = {
    background: {
      color: {
        value: 'transparent',
      },
    },
    fpsLimit: 30,
    particles: {
      number: {
        value: getParticleCount(),
        density: {
          enable: false,
        },
      },
      color: {
        value: '#ff1493',
      },
      shape: {
        type: 'circle',
      },
      opacity: {
        value: 0.3,
      },
      size: {
        value: { min: 1, max: 3 },
      },
      links: {
        enable: false,
      },
      move: {
        enable: false,
      },
    },
    interactivity: {
      events: {
        onHover: {
          enable: false,
        },
      },
    },
    detectRetina: true,
  };

  if (!engineReady || performanceMode) {
    return null;
  }

  return (
    <Particles
      id="particle-background"
      options={prefersReducedMotion ? reducedOptions : fullOptions}
      particlesLoaded={particlesLoaded}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
}
