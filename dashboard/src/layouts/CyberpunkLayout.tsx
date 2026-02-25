import { Outlet } from 'react-router-dom';
import { NeonSidebar } from '../components/cyber';
import { ParticleBackground } from '../components/effects/ParticleBackground';
import { PageTransition } from '../components/effects/PageTransition';

export function CyberpunkLayout() {
  return (
    <div className="flex h-screen bg-cyber-void text-cyber-text scanlines">
      <ParticleBackground />
      <NeonSidebar />
      <main className="flex-1 overflow-y-auto p-6">
        <PageTransition>
          <Outlet />
        </PageTransition>
      </main>
    </div>
  );
}
