import { useCallback, useEffect, useState } from 'react';
import Particles, { initParticlesEngine } from '@tsparticles/react';
import type { ISourceOptions } from '@tsparticles/engine';
import { loadSlim } from '@tsparticles/slim';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { usePerformanceMode } from '../../hooks/usePerformanceMode';

function getParticleCount(): number {
  const width = window.innerWidth;
  if (width >= 1024) return 180;
  if (width >= 768) return 100;
  return 60;
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
    // no-op
  }, []);

  const fullOptions: ISourceOptions = {
    background: {
      color: { value: 'transparent' },
    },
    fpsLimit: 60,
    particles: {
      number: {
        value: getParticleCount(),
        density: { enable: false },
      },
      color: {
        value: ['#ff1493', '#ff4040', '#ff6b35', '#9b30ff', '#c850c0'],
      },
      shape: { type: 'circle' },
      opacity: {
        value: { min: 0.15, max: 0.6 },
        animation: {
          enable: true,
          speed: 0.8,
          sync: false,
        },
      },
      size: {
        value: { min: 1, max: 4 },
        animation: {
          enable: true,
          speed: 2,
          sync: false,
        },
      },
      links: {
        enable: true,
        distance: 140,
        color: { value: '#ff1493' },
        opacity: 0.12,
        width: 1,
        triangles: {
          enable: true,
          opacity: 0.02,
        },
      },
      move: {
        enable: true,
        speed: { min: 0.8, max: 2.5 },
        direction: 'none',
        random: true,
        straight: false,
        outModes: { default: 'bounce' },
        attract: {
          enable: true,
          rotate: { x: 600, y: 1200 },
        },
      },
    },
    interactivity: {
      events: {
        onHover: {
          enable: true,
          mode: ['grab', 'repulse'],
        },
      },
      modes: {
        grab: {
          distance: 180,
          links: {
            opacity: 0.35,
            color: '#ff6b35',
          },
        },
        repulse: {
          distance: 80,
          duration: 0.3,
        },
      },
    },
    detectRetina: true,
  };

  const reducedOptions: ISourceOptions = {
    background: {
      color: { value: 'transparent' },
    },
    fpsLimit: 30,
    particles: {
      number: {
        value: Math.round(getParticleCount() * 0.5),
        density: { enable: false },
      },
      color: {
        value: ['#ff1493', '#ff4040', '#ff6b35', '#9b30ff', '#c850c0'],
      },
      shape: { type: 'circle' },
      opacity: { value: 0.3 },
      size: { value: { min: 1, max: 3 } },
      links: { enable: false },
      move: { enable: false },
    },
    interactivity: {
      events: {
        onHover: { enable: false },
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
