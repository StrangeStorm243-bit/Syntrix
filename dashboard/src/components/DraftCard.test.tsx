import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { DraftCard } from './DraftCard';
import type { DraftItem } from '../hooks/useQueue';

const draft: DraftItem = {
  id: 1,
  normalized_post_id: 10,
  project_id: 'spectra',
  text_generated: 'Hey! Check out Spectra!',
  text_final: null,
  tone: 'helpful',
  template_used: null,
  model_id: 'claude-sonnet-4-6',
  status: 'pending',
  created_at: null,
  approved_at: null,
  sent_at: null,
  author_username: 'alice',
  author_display_name: 'Alice',
  text_original: 'Looking for a CRM tool',
  score: 82.5,
};

describe('DraftCard', () => {
  it('renders draft text and author', () => {
    render(
      <DraftCard draft={draft} onApprove={vi.fn()} onEdit={vi.fn()} onReject={vi.fn()} />,
    );
    expect(screen.getByText('Hey! Check out Spectra!')).toBeInTheDocument();
    expect(screen.getByText('@alice')).toBeInTheDocument();
  });

  it('calls onApprove when approve button clicked', async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn();
    render(
      <DraftCard draft={draft} onApprove={onApprove} onEdit={vi.fn()} onReject={vi.fn()} />,
    );

    await user.click(screen.getByText('Approve'));
    expect(onApprove).toHaveBeenCalledWith(1);
  });

  it('calls onReject when reject button clicked', async () => {
    const user = userEvent.setup();
    const onReject = vi.fn();
    render(
      <DraftCard draft={draft} onApprove={vi.fn()} onEdit={vi.fn()} onReject={onReject} />,
    );

    await user.click(screen.getByText('Reject'));
    expect(onReject).toHaveBeenCalledWith(1, '');
  });

  it('enters edit mode and saves', async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    render(
      <DraftCard draft={draft} onApprove={vi.fn()} onEdit={onEdit} onReject={vi.fn()} />,
    );

    await user.click(screen.getByText('Edit'));
    // Should show textarea with draft text
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveValue('Hey! Check out Spectra!');

    // Clear and type new text
    await user.clear(textarea);
    await user.type(textarea, 'Updated reply');

    await user.click(screen.getByText('Save'));
    expect(onEdit).toHaveBeenCalledWith(1, 'Updated reply');
  });

  it('cancels edit mode', async () => {
    const user = userEvent.setup();
    render(
      <DraftCard draft={draft} onApprove={vi.fn()} onEdit={vi.fn()} onReject={vi.fn()} />,
    );

    await user.click(screen.getByText('Edit'));
    expect(screen.getByRole('textbox')).toBeInTheDocument();

    await user.click(screen.getByText('Cancel'));
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('shows original post text', () => {
    render(
      <DraftCard draft={draft} onApprove={vi.fn()} onEdit={vi.fn()} onReject={vi.fn()} />,
    );
    expect(screen.getByText('Looking for a CRM tool')).toBeInTheDocument();
  });
});
