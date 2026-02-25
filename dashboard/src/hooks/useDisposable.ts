import { useEffect, useRef } from 'react';
import type { Mesh } from 'three';

export function useDisposable<T extends Mesh>() {
  const ref = useRef<T>(null);

  useEffect(() => {
    return () => {
      if (ref.current) {
        ref.current.geometry?.dispose();

        if (Array.isArray(ref.current.material)) {
          ref.current.material.forEach((m) => m.dispose());
        } else {
          ref.current.material?.dispose();
        }
      }
    };
  }, []);

  return ref;
}
