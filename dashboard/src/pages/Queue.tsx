import { DraftCard } from '../components/DraftCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { useQueue, useApproveDraft, useEditDraft, useRejectDraft } from '../hooks/useQueue';

export default function Queue() {
  const { data, isLoading } = useQueue();
  const approve = useApproveDraft();
  const edit = useEditDraft();
  const reject = useRejectDraft();

  if (isLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  const drafts = data?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Approval Queue</h1>
        <span className="text-sm text-gray-400">{data?.total ?? 0} pending</span>
      </div>

      {drafts.length === 0 ? (
        <EmptyState title="Queue empty" description="No drafts waiting for approval." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {drafts.map((draft) => (
            <DraftCard
              key={draft.id}
              draft={draft}
              onApprove={(id) => approve.mutate(id)}
              onEdit={(id, text) => edit.mutate({ id, text })}
              onReject={(id, reason) => reject.mutate({ id, reason })}
            />
          ))}
        </div>
      )}
    </div>
  );
}
