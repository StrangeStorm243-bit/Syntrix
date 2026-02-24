import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { useExperiments } from '../hooks/useExperiments';

export default function Experiments() {
  const { data: experiments, isLoading } = useExperiments();

  if (isLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">A/B Experiments</h1>

      {!experiments || experiments.length === 0 ? (
        <EmptyState
          title="No experiments"
          description="Create an A/B experiment to compare model performance."
        />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-700">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-700 bg-gray-800/50 text-left text-gray-400">
              <tr>
                <th className="px-4 py-3">Experiment</th>
                <th className="px-4 py-3">Primary</th>
                <th className="px-4 py-3">Canary</th>
                <th className="px-4 py-3">Traffic %</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {experiments.map((exp) => (
                <tr key={exp.experiment_id} className="hover:bg-gray-800/30">
                  <td className="px-4 py-3 font-medium text-white">{exp.experiment_id}</td>
                  <td className="px-4 py-3 text-gray-300">{exp.primary_model}</td>
                  <td className="px-4 py-3 text-gray-300">{exp.canary_model}</td>
                  <td className="px-4 py-3 text-gray-400">{(exp.canary_pct * 100).toFixed(0)}%</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        exp.status === 'active'
                          ? 'bg-green-900/50 text-green-400'
                          : 'bg-gray-700 text-gray-400'
                      }`}
                    >
                      {exp.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
