import { useState } from 'react';
import { Send, Loader2, Check } from 'lucide-react';
import { DraftCard } from '../components/DraftCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { FlipCard } from '../components/cyber/FlipCard';
import { useQueue, useApproveDraft, useEditDraft, useRejectDraft, useSendDrafts } from '../hooks/useQueue';

export default function Queue() {
  const { data, isLoading } = useQueue();
  const approve = useApproveDraft();
  const edit = useEditDraft();
  const reject = useRejectDraft();
  const sendDrafts = useSendDrafts();
  const [sendResult, setSendResult] = useState<{ sent: number; failed: number } | null>(null);

  if (isLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  const drafts = data?.items ?? [];
  const approvedCount = drafts.filter((d) => d.status === 'approved').length;

  function handleSend() {
    setSendResult(null);
    sendDrafts.mutate(undefined, {
      onSuccess: (res) => {
        setSendResult({ sent: res.sent_count, failed: res.failed_count });
        setTimeout(() => setSendResult(null), 5000);
      },
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Approval Queue</h1>
        <div className="flex items-center gap-3">
          {sendResult && (
            <span className="flex items-center gap-1.5 text-xs text-green-400">
              <Check size={14} />
              {sendResult.sent} sent{sendResult.failed > 0 ? `, ${sendResult.failed} failed` : ''}
            </span>
          )}
          {approvedCount > 0 && (
            <button
              type="button"
              onClick={handleSend}
              disabled={sendDrafts.isPending}
              className="flex items-center gap-2 rounded-lg border border-cyber-pink bg-cyber-pink/10 px-4 py-2 text-xs font-mono text-cyber-pink transition-all hover:bg-cyber-pink/20 hover:shadow-[0_0_12px_rgba(255,20,147,0.4)] disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {sendDrafts.isPending ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send size={14} />
                  Send {approvedCount} Approved
                </>
              )}
            </button>
          )}
          <span className="text-sm text-gray-400">{data?.total ?? 0} pending</span>
        </div>
      </div>

      <FlipCard
        frontSrc="/images/thread-front.png"
        backSrc="/images/thread-back.png"
        alt="The Thread"
        className="h-40 w-full"
        autoFlipInterval={5000}
      />

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
