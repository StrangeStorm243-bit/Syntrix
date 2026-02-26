import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CyberpunkLayout } from './layouts/CyberpunkLayout';
import { useSetupStatus } from './hooks/useSetup';
import { LoadingSpinner } from './components/LoadingSpinner';
import Dashboard from './pages/Dashboard';
import Leads from './pages/Leads';
import Queue from './pages/Queue';
import Analytics from './pages/Analytics';
import Experiments from './pages/Experiments';
import Settings from './pages/Settings';
import PipelineLive from './pages/PipelineLive';
import Sequences from './pages/Sequences';
import Onboarding from './pages/Onboarding';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function AppRoutes() {
  const { data: setupStatus, isLoading, isError } = useSetupStatus();

  // While checking setup status, show a loading state
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cyber-void">
        <LoadingSpinner className="mx-auto" />
      </div>
    );
  }

  // If setup check fails (API not ready), show the dashboard anyway
  // This allows development without the backend running
  const isSetupComplete = isError || setupStatus?.is_complete === true;

  if (!isSetupComplete) {
    return <Onboarding />;
  }

  return (
    <Routes>
      <Route element={<CyberpunkLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="leads" element={<Leads />} />
        <Route path="queue" element={<Queue />} />
        <Route path="sequences" element={<Sequences />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="experiments" element={<Experiments />} />
        <Route path="settings" element={<Settings />} />
        <Route path="pipeline" element={<PipelineLive />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
