import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/projects', () =>
    HttpResponse.json([
      { id: 'spectra', name: 'Spectra', config_path: 'projects/spectra.yaml', is_active: true, created_at: null, updated_at: null },
    ]),
  ),

  http.get('/api/stats', () =>
    HttpResponse.json({
      collected: 100, judged: 80, relevant: 50, scored: 50, drafted: 30, approved: 20, sent: 10, outcomes: 5,
    }),
  ),

  http.get('/api/leads', () =>
    HttpResponse.json({
      items: [
        {
          id: 1, platform: 'x', platform_id: 'tweet_1', author_username: 'alice',
          author_display_name: 'Alice', author_followers: 500, author_verified: true,
          text_original: 'Looking for a CRM tool', text_cleaned: 'looking for a crm tool',
          created_at: '2026-01-15T00:00:00Z', score: 82.5, judgment_label: 'relevant',
          judgment_confidence: 0.95, draft_status: 'pending',
        },
      ],
      total: 1, page: 1, page_size: 20, pages: 1,
    }),
  ),

  http.get('/api/queue', () =>
    HttpResponse.json({
      items: [
        {
          id: 1, normalized_post_id: 1, project_id: 'spectra',
          text_generated: 'Hey! Have you checked out Spectra?', text_final: null,
          tone: 'helpful', template_used: null, model_id: 'claude-sonnet-4-6',
          status: 'pending', created_at: null, approved_at: null, sent_at: null,
          author_username: 'alice', author_display_name: 'Alice',
          text_original: 'Looking for a CRM tool', score: 82.5,
        },
      ],
      total: 1, page: 1, page_size: 20, pages: 1,
    }),
  ),

  http.post('/api/queue/:id/approve', () =>
    HttpResponse.json({
      id: 1, normalized_post_id: 1, project_id: 'spectra',
      text_generated: 'Hey! Have you checked out Spectra?',
      text_final: 'Hey! Have you checked out Spectra?',
      tone: 'helpful', template_used: null, model_id: 'claude-sonnet-4-6',
      status: 'approved', created_at: null, approved_at: '2026-02-24T12:00:00Z',
      sent_at: null, author_username: 'alice', author_display_name: 'Alice',
      text_original: 'Looking for a CRM tool', score: 82.5,
    }),
  ),

  http.post('/api/queue/:id/reject', () =>
    HttpResponse.json({
      id: 1, normalized_post_id: 1, project_id: 'spectra',
      text_generated: 'Hey!', text_final: null, tone: 'helpful',
      template_used: null, model_id: 'claude-sonnet-4-6',
      status: 'rejected', created_at: null, approved_at: null, sent_at: null,
      author_username: 'alice', author_display_name: 'Alice',
      text_original: 'Looking for a CRM tool', score: 82.5,
    }),
  ),

  http.get('/api/analytics/score-distribution', () =>
    HttpResponse.json([
      { bucket_min: 70, bucket_max: 80, count: 3 },
      { bucket_min: 80, bucket_max: 90, count: 5 },
    ]),
  ),

  http.get('/api/analytics/conversion-funnel', () =>
    HttpResponse.json([
      { stage: 'Collected', count: 100 },
      { stage: 'Judged', count: 80 },
      { stage: 'Scored', count: 50 },
      { stage: 'Drafted', count: 30 },
      { stage: 'Sent', count: 10 },
      { stage: 'Outcome', count: 5 },
    ]),
  ),

  http.get('/api/experiments', () => HttpResponse.json([])),
];
