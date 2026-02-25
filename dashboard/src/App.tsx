import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CyberpunkLayout } from './layouts/CyberpunkLayout';
import Dashboard from './pages/Dashboard';
import Leads from './pages/Leads';
import Queue from './pages/Queue';
import Analytics from './pages/Analytics';
import Experiments from './pages/Experiments';
import Settings from './pages/Settings';
import PipelineLive from './pages/PipelineLive';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<CyberpunkLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="leads" element={<Leads />} />
            <Route path="queue" element={<Queue />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="experiments" element={<Experiments />} />
            <Route path="settings" element={<Settings />} />
            <Route path="pipeline" element={<PipelineLive />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
