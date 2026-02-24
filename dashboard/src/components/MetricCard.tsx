import { formatNumber } from '../lib/utils';

interface MetricCardProps {
  label: string;
  value: number;
  icon?: React.ReactNode;
}

export function MetricCard({ label, value, icon }: MetricCardProps) {
  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">{label}</p>
        {icon && <span className="text-gray-500">{icon}</span>}
      </div>
      <p className="mt-2 text-2xl font-semibold text-white">{formatNumber(value)}</p>
    </div>
  );
}
