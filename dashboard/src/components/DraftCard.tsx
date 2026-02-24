import { useState } from 'react';
import { Check, Edit3, X } from 'lucide-react';
import { ScoreBadge } from './ScoreBadge';
import type { DraftItem } from '../hooks/useQueue';

interface DraftCardProps {
  draft: DraftItem;
  onApprove: (id: number) => void;
  onEdit: (id: number, text: string) => void;
  onReject: (id: number, reason: string) => void;
}

export function DraftCard({ draft, onApprove, onEdit, onReject }: DraftCardProps) {
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(draft.text_generated);

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4 space-y-3">
      {/* Original post */}
      <div className="text-sm text-gray-400">
        <span className="font-medium text-gray-300">
          @{draft.author_username || 'unknown'}
        </span>
        {draft.text_original && (
          <p className="mt-1 text-gray-500 line-clamp-2">{draft.text_original}</p>
        )}
      </div>

      {/* Score */}
      <div className="flex items-center gap-2">
        <ScoreBadge score={draft.score} />
        <span className="text-xs text-gray-500">{draft.model_id}</span>
      </div>

      {/* Draft text */}
      {editing ? (
        <textarea
          className="w-full rounded border border-gray-600 bg-gray-900 p-2 text-sm text-white"
          rows={3}
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
        />
      ) : (
        <p className="text-sm text-white">{draft.text_generated}</p>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        {editing ? (
          <>
            <button
              onClick={() => { onEdit(draft.id, editText); setEditing(false); }}
              className="flex items-center gap-1 rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
            >
              <Check size={14} /> Save
            </button>
            <button
              onClick={() => setEditing(false)}
              className="rounded border border-gray-600 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => onApprove(draft.id)}
              className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700"
            >
              <Check size={14} /> Approve
            </button>
            <button
              onClick={() => setEditing(true)}
              className="flex items-center gap-1 rounded border border-gray-600 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700"
            >
              <Edit3 size={14} /> Edit
            </button>
            <button
              onClick={() => onReject(draft.id, '')}
              className="flex items-center gap-1 rounded border border-red-800 px-3 py-1.5 text-xs text-red-400 hover:bg-red-900/30"
            >
              <X size={14} /> Reject
            </button>
          </>
        )}
      </div>
    </div>
  );
}
