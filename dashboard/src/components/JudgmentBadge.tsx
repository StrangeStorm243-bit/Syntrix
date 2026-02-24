import { cn } from '../lib/utils';

const COLORS: Record<string, string> = {
  relevant: 'bg-green-900/50 text-green-400',
  irrelevant: 'bg-red-900/50 text-red-400',
  maybe: 'bg-yellow-900/50 text-yellow-400',
};

export function JudgmentBadge({ label }: { label: string | null }) {
  if (!label) return <span className="text-gray-500">--</span>;
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize',
        COLORS[label] || 'bg-gray-800 text-gray-400',
      )}
    >
      {label}
    </span>
  );
}
