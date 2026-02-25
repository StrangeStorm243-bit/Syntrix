import { lazy, Suspense, type ComponentType, type ReactNode } from 'react';

/**
 * Lazy-load a 3D/heavy component. Wraps React.lazy with proper typing.
 * Use for all R3F, Three.js, and post-processing imports.
 *
 * @example
 * const HeroScene = lazy3D(() => import('./scenes/HeroScene'));
 */
export function lazy3D<P extends object>(
  factory: () => Promise<{ default: ComponentType<P> }>,
) {
  return lazy(factory);
}

/**
 * Suspense boundary for 3D content.
 * Provides a consistent loading fallback for all lazy-loaded 3D components.
 */
export function Suspense3D({
  children,
  fallback = null,
}: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  return <Suspense fallback={fallback}>{children}</Suspense>;
}

/*
 * ARCHITECTURE NOTES (for future phases):
 *
 * 1. SINGLE CANVAS STRATEGY
 *    Use ONE <Canvas> at the CyberpunkLayout level.
 *    Never create per-page Canvas components.
 *    Browsers limit WebGL contexts to ~8-16; exceeding this crashes existing contexts.
 *
 * 2. REF-BASED ANIMATION CONVENTION
 *    Inside useFrame(), ALWAYS use useRef to mutate Three.js objects.
 *    NEVER call setState/dispatch inside useFrame() — it triggers React re-renders at 60fps.
 *
 *    GOOD:
 *      const meshRef = useRef<Mesh>(null);
 *      useFrame((_, delta) => { meshRef.current!.rotation.y += delta; });
 *
 *    BAD:
 *      const [rotation, setRotation] = useState(0);
 *      useFrame((_, delta) => { setRotation(r => r + delta); }); // 60 re-renders/sec!
 *
 * 3. LAZY LOADING
 *    All R3F/Three.js imports MUST go through lazy3D() or dynamic import().
 *    Target: initial bundle under 200KB (Three.js alone is ~500KB gzipped).
 */
