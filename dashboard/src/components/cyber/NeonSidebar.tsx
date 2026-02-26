import { NavLink } from 'react-router-dom';
import { motion } from 'motion/react';
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  BarChart3,
  FlaskConical,
  Settings,
  GitBranch,
  Workflow,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { slideUp } from '../../lib/animation-presets';

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/leads', icon: Users, label: 'Leads' },
  { to: '/queue', icon: MessageSquare, label: 'Queue' },
  { to: '/sequences', icon: Workflow, label: 'Sequences' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/experiments', icon: FlaskConical, label: 'Experiments' },
  { to: '/pipeline', icon: GitBranch, label: 'Pipeline' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export function NeonSidebar() {
  return (
    <motion.aside
      initial="hidden"
      animate="visible"
      variants={slideUp}
      className="glass flex h-screen w-56 flex-col border-r border-white/10"
    >
      {/* Brand area */}
      <div className="flex h-14 items-center px-5 border-b border-white/10">
        <span
          className="neon-glow text-lg font-bold tracking-widest text-cyber-pink uppercase"
          style={{
            textShadow:
              '0 0 8px var(--cyber-glow-pink), 0 0 20px var(--cyber-glow-pink)',
          }}
        >
          Syntrix
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5 p-2 pt-3">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'group relative flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'text-cyber-pink'
                  : 'text-cyber-text-dim hover:text-cyber-text',
              )
            }
          >
            {({ isActive }) => (
              <>
                {/* Active left-border glow indicator */}
                {isActive && (
                  <span
                    className="absolute left-0 inset-y-1 w-0.5 rounded-full bg-cyber-pink"
                    style={{
                      boxShadow:
                        '0 0 6px var(--cyber-glow-pink), 0 0 12px var(--cyber-glow-pink)',
                    }}
                  />
                )}

                {/* Hover background glow */}
                <span
                  className={cn(
                    'absolute inset-0 rounded-md transition-opacity duration-200',
                    isActive
                      ? 'opacity-100 bg-cyber-pink/10'
                      : 'opacity-0 group-hover:opacity-100 bg-white/5',
                  )}
                />

                {/* Icon */}
                <Icon
                  size={17}
                  className={cn(
                    'relative z-10 shrink-0 transition-all duration-200',
                    isActive
                      ? 'text-cyber-pink'
                      : 'text-cyber-text-dim group-hover:text-cyber-text',
                  )}
                  style={
                    isActive
                      ? {
                          filter:
                            'drop-shadow(0 0 4px var(--cyber-glow-pink))',
                        }
                      : undefined
                  }
                />

                {/* Label */}
                <span className="relative z-10">{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </motion.aside>
  );
}
