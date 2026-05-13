import React from 'react';
import { BrowserRouter, Routes, Route, Outlet, useNavigate, useParams } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import AppShell from '@/components/cockpit/AppShell';
import Dashboard from '@/pages/Dashboard';
import NewProject from '@/pages/NewProject';
import Cockpit from '@/pages/Cockpit';
import BRDPage from '@/pages/BRD';
import ArchitecturePage from '@/pages/Architecture';
import PlanPage from '@/pages/Plan';
import FilesPage from '@/pages/Files';
import BuildPage from '@/pages/Build';
import AcceptancePage from '@/pages/Acceptance';
import ExportPage from '@/pages/Export';
import useProject from '@/lib/useProject';
import '@/App.css';

function GlobalShell() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

function ProjectShell() {
  const { id } = useParams();
  const { project, refresh } = useProject(id);
  if (!project) {
    return (
      <AppShell>
        <div className="surface-1 p-8 text-center">
          <div className="text-sm text-muted-foreground">Loading project…</div>
        </div>
      </AppShell>
    );
  }
  return (
    <AppShell project={project}>
      <Outlet context={{ project, refresh }} />
    </AppShell>
  );
}

function NotFound() {
  const nav = useNavigate();
  return (
    <AppShell>
      <div className="surface-1 p-8">
        <div className="text-lg font-semibold">Not Found</div>
        <button onClick={() => nav('/')} className="mt-3 text-sm text-[hsl(var(--link))]">← Back to Dashboard</button>
      </div>
    </AppShell>
  );
}

function App() {
  React.useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route element={<GlobalShell />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects/new" element={<NewProject />} />
          </Route>
          <Route path="/projects/:id" element={<ProjectShell />}>
            <Route index element={<Cockpit />} />
            <Route path="brd" element={<BRDPage />} />
            <Route path="architecture" element={<ArchitecturePage />} />
            <Route path="plan" element={<PlanPage />} />
            <Route path="files" element={<FilesPage />} />
            <Route path="build" element={<BuildPage />} />
            <Route path="acceptance" element={<AcceptancePage />} />
            <Route path="export" element={<ExportPage />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
      <Toaster theme="dark" />
    </div>
  );
}

export default App;
