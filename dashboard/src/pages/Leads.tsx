import { useState } from 'react';
import { useLeads } from '../hooks/useLeads';
import { ScoreBadge } from '../components/ScoreBadge';
import { JudgmentBadge } from '../components/JudgmentBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { FlipCard } from '../components/cyber/FlipCard';

export default function Leads() {
  const [page, setPage] = useState(1);
  const [label, setLabel] = useState('');
  const params: Record<string, string> = { page: String(page), page_size: '20' };
  if (label) params.label = label;

  const { data, isLoading } = useLeads(params);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Leads</h1>
        <select
          value={label}
          onChange={(e) => { setLabel(e.target.value); setPage(1); }}
          className="rounded border border-gray-600 bg-gray-800 px-3 py-1.5 text-sm text-white"
        >
          <option value="">All labels</option>
          <option value="relevant">Relevant</option>
          <option value="irrelevant">Irrelevant</option>
          <option value="maybe">Maybe</option>
        </select>
      </div>

      <FlipCard
        frontSrc="/images/doorway-front.png"
        backSrc="/images/doorway-back.png"
        alt="The Doorway"
        className="h-40 w-full"
        autoFlipInterval={6500}
      />

      {isLoading ? (
        <LoadingSpinner className="mx-auto mt-10" />
      ) : !data || data.items.length === 0 ? (
        <EmptyState title="No leads found" description="Run the pipeline to collect leads." />
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-gray-700">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-700 bg-gray-800/50 text-left text-gray-400">
                <tr>
                  <th className="px-4 py-3">Author</th>
                  <th className="px-4 py-3">Text</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Judgment</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {data.items.map((lead) => (
                  <tr key={lead.id} className="hover:bg-gray-800/30">
                    <td className="px-4 py-3 font-medium text-white">
                      @{lead.author_username || 'unknown'}
                    </td>
                    <td className="max-w-md truncate px-4 py-3 text-gray-300">
                      {lead.text_cleaned}
                    </td>
                    <td className="px-4 py-3"><ScoreBadge score={lead.score} /></td>
                    <td className="px-4 py-3"><JudgmentBadge label={lead.judgment_label} /></td>
                    <td className="px-4 py-3 text-gray-400">{lead.draft_status || '--'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>{data.total} leads total</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="rounded border border-gray-600 px-3 py-1 disabled:opacity-50"
              >
                Prev
              </button>
              <span className="px-2 py-1">
                {page} / {data.pages}
              </span>
              <button
                disabled={page >= data.pages}
                onClick={() => setPage(page + 1)}
                className="rounded border border-gray-600 px-3 py-1 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
