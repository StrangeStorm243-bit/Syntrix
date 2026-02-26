import { NavLink } from 'react-router-dom';
import { motion } from 'motion/react';
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  BarChart3,
  FlaskConical,
  Settings,
  Info,
  Workflow,
  Github,
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
  { to: '/how-it-works', icon: Info, label: 'How It Works' },
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
        <span
          className="ml-2 rounded-full px-2 py-0.5 text-[10px] font-mono font-medium"
          style={{
            background: 'rgba(255,20,147,0.12)',
            border: '1px solid rgba(255,20,147,0.25)',
            color: 'var(--cyber-pink)',
          }}
        >
          v0.3
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

      {/* Open Source — GitHub link */}
      <div className="border-t border-white/10 p-3">
        <a
          href="https://github.com/StrangeStorm243-bit/Syntrix"
          target="_blank"
          rel="noopener noreferrer"
          className="group relative flex items-center gap-3 rounded-lg px-3 py-2.5 transition-all duration-300 hover:scale-[1.02]"
          style={{
            background: 'linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,20,147,0.08))',
            border: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <span
            className="absolute inset-0 rounded-lg opacity-0 transition-opacity duration-300 group-hover:opacity-100"
            style={{
              background: 'linear-gradient(135deg, rgba(255,20,147,0.15), rgba(255,165,0,0.1))',
              boxShadow: '0 0 20px rgba(255,20,147,0.15), inset 0 0 20px rgba(255,20,147,0.05)',
            }}
          />
          <Github
            size={18}
            className="relative z-10 text-white transition-all duration-300 group-hover:text-cyber-pink"
            style={{ filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.3))' }}
          />
          <div className="relative z-10 flex flex-col">
            <span className="text-xs font-semibold text-white/90 group-hover:text-cyber-pink transition-colors duration-300">
              Open Source
            </span>
            <span className="text-[10px] text-cyber-text-dim">
              Star us on GitHub
            </span>
          </div>
          <span className="relative z-10 ml-auto text-xs text-cyber-text-dim group-hover:text-cyber-pink transition-colors duration-300">
            &#8599;
          </span>
        </a>
      </div>
    </motion.aside>
  );
}
