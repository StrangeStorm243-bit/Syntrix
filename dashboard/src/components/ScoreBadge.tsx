import { cn } from '../lib/utils';

export function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-gray-500">--</span>;

  const color =
    score >= 70 ? 'bg-green-900/50 text-green-400' :
    score >= 40 ? 'bg-yellow-900/50 text-yellow-400' :
    'bg-red-900/50 text-red-400';

  return (
    <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', color)}>
      {score.toFixed(0)}
    </span>
  );
}
