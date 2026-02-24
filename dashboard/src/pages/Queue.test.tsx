import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import Queue from './Queue';

const QUEUE_ITEMS = [
  {
    id: 1, normalized_post_id: 1, project_id: 'spectra',
    text_generated: 'Hey! Have you checked out Spectra?', text_final: null,
    tone: 'helpful', template_used: null, model_id: 'claude-sonnet-4-6',
    status: 'pending', created_at: null, approved_at: null, sent_at: null,
    author_username: 'alice', author_display_name: 'Alice',
    text_original: 'Looking for a CRM tool', score: 82.5,
  },
];

vi.mock('../lib/api', () => ({
  apiGet: vi.fn(async () => ({
    items: QUEUE_ITEMS,
    total: 1,
    page: 1,
    page_size: 20,
    pages: 1,
  })),
  apiPost: vi.fn(async () => ({ ...QUEUE_ITEMS[0], status: 'approved' })),
  setApiKey: vi.fn(),
  getStoredApiKey: vi.fn(() => ''),
  ApiError: class extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

function renderQueue() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Queue />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Queue Page', () => {
  it('renders drafts after loading', async () => {
    renderQueue();
    await waitFor(() => {
      expect(screen.getByText('@alice')).toBeInTheDocument();
    });
  });

  it('displays draft text', async () => {
    renderQueue();
    await waitFor(() => {
      expect(screen.getByText('Hey! Have you checked out Spectra?')).toBeInTheDocument();
    });
  });

  it('shows pending count', async () => {
    renderQueue();
    await waitFor(() => {
      expect(screen.getByText('1 pending')).toBeInTheDocument();
    });
  });

  it('shows action buttons', async () => {
    renderQueue();
    await waitFor(() => {
      expect(screen.getByText('Approve')).toBeInTheDocument();
      expect(screen.getByText('Reject')).toBeInTheDocument();
      expect(screen.getByText('Edit')).toBeInTheDocument();
    });
  });

  it('can click approve button without error', async () => {
    const user = userEvent.setup();
    renderQueue();
    await waitFor(() => {
      expect(screen.getByText('Approve')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Approve'));
    // Verify no crash occurred — the mutation fires
  });
});
