import { useState } from 'react';
import type { ReactNode } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { staggerContainer, slideUp } from '../../lib/animation-presets';
import { cn } from '../../lib/utils';

export interface NeonColumn<T> {
  key: string;
  header: string;
  render?: (row: T) => ReactNode;
  className?: string;
  mono?: boolean;
}

interface NeonTableProps<T> {
  columns: NeonColumn<T>[];
  data: T[];
  keyField: keyof T;
  className?: string;
  emptyMessage?: string;
  pageSize?: number;
  onRowClick?: (row: T) => void;
}

/**
 * Table with neon-styled headers, glass header row, glow row highlights on
 * hover, monospace numeric columns, stagger row animation, and pagination.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function NeonTable<T extends Record<string, any>>({
  columns,
  data,
  keyField,
  className,
  emptyMessage = 'No data yet',
  pageSize = 10,
  onRowClick,
}: NeonTableProps<T>) {
  const [page, setPage] = useState(0);

  const totalPages = Math.max(1, Math.ceil(data.length / pageSize));
  const pageStart = page * pageSize;
  const pageEnd = pageStart + pageSize;
  const pageData = data.slice(pageStart, pageEnd);

  if (data.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-cyber-text-dim">{emptyMessage}</p>
    );
  }

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          {/* Glass header row with neon bottom border */}
          <thead className="glass-strong">
            <tr className="border-b-2 border-cyber-pink/30">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-cyber-pink',
                    col.className,
                  )}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>

          {/* Stagger-animated body */}
          <AnimatePresence mode="wait">
            <motion.tbody
              key={page}
              className="divide-y divide-cyber-pink/10"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              {pageData.map((row) => (
                <motion.tr
                  key={String(row[keyField])}
                  variants={slideUp}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={cn(
                    'group relative transition-colors',
                    'hover:bg-cyber-pink/5',
                    // Left border glow on hover via a pseudo-element substitute:
                    // We use box-shadow inset on the row itself as a left-border glow.
                    'hover:shadow-[inset_3px_0_0_0_rgba(255,20,147,0.6)]',
                    onRowClick && 'cursor-pointer',
                  )}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        'px-4 py-3 text-cyber-text',
                        col.mono && 'font-mono',
                        col.className,
                      )}
                    >
                      {col.render ? col.render(row) : String(row[col.key] ?? '')}
                    </td>
                  ))}
                </motion.tr>
              ))}
            </motion.tbody>
          </AnimatePresence>
        </table>
      </div>

      {/* Pagination controls — only rendered when there is more than one page */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-1">
          <span className="text-xs text-cyber-text-dim">
            {pageStart + 1}–{Math.min(pageEnd, data.length)} of {data.length}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className={cn(
                'rounded border border-cyber-pink/30 px-3 py-1 text-xs text-cyber-pink',
                'transition-all hover:border-cyber-pink/60 hover:bg-cyber-pink/10',
                'disabled:cursor-not-allowed disabled:opacity-30',
              )}
            >
              Prev
            </button>
            <button
              type="button"
              disabled={page === totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className={cn(
                'rounded border border-cyber-pink/30 px-3 py-1 text-xs text-cyber-pink',
                'transition-all hover:border-cyber-pink/60 hover:bg-cyber-pink/10',
                'disabled:cursor-not-allowed disabled:opacity-30',
              )}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
