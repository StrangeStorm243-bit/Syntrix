import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';

export function CyberpunkLayout() {
  return (
    <div className="flex h-screen bg-cyber-void text-cyber-text scanlines">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
