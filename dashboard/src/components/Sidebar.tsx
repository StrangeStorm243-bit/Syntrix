import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  BarChart3,
  FlaskConical,
  Settings,
  Activity,
  Workflow,
} from 'lucide-react';
import { cn } from '../lib/utils';

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/leads', icon: Users, label: 'Leads' },
  { to: '/queue', icon: MessageSquare, label: 'Queue' },
  { to: '/sequences', icon: Workflow, label: 'Sequences' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/experiments', icon: FlaskConical, label: 'Experiments' },
  { to: '/pipeline', icon: Activity, label: 'Pipeline' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-56 flex-col border-r border-gray-700 bg-gray-900">
      <div className="flex h-14 items-center px-4 border-b border-gray-700">
        <span className="text-lg font-bold text-white">Syntrix</span>
      </div>
      <nav className="flex-1 space-y-1 p-2">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200',
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
