import { Wifi, WifiOff } from 'lucide-react';
import { ProjectSelector } from './ProjectSelector';

interface TopBarProps {
  connected: boolean;
  projects: { id: string; name: string }[];
  activeProject: string | null;
  onProjectChange: (id: string) => void;
}

export function TopBar({ connected, projects, activeProject, onProjectChange }: TopBarProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-700 bg-gray-900/50 px-6">
      <ProjectSelector
        projects={projects}
        activeProject={activeProject}
        onChange={onProjectChange}
      />
      <div className="flex items-center gap-2 text-sm">
        {connected ? (
          <span className="flex items-center gap-1.5 text-green-400">
            <Wifi size={14} /> Connected
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-gray-500">
            <WifiOff size={14} /> Disconnected
          </span>
        )}
      </div>
    </header>
  );
}
