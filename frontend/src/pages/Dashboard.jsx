import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Activity, FolderGit2, AlertCircle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import StatePill from '@/components/cockpit/StatePill';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

export default function Dashboard() {
  const [projects, setProjects] = useState(null);
  const [error, setError] = useState(null);
  const nav = useNavigate();

  useEffect(() => {
    let alive = true;
    const load = () => api.listProjects()
      .then(p => { if (alive) { setProjects(p); setError(null); } })
      .catch(e => { if (alive) setError(e); });
    load();
    const t = setInterval(load, 4000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      {/* Hero / CTA */}
      <div className="surface-1 p-6 sm:p-8 flex flex-col gap-2 relative overflow-hidden">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[hsl(var(--primary)/0.18)] border border-[hsl(var(--primary)/0.35)]">
            <Activity className="h-6 w-6 text-[hsl(var(--primary))]" />
          </div>
          <div className="flex-1">
            <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">Local App Creator</h1>
            <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
              A local-first AI software-factory cockpit. Describe what you need, answer SME-style
              clarifications, and generate <strong>real</strong> React+Vite + FastAPI + SQLite
              applications you can run on your own machine. No fake APIs, no silent fallbacks.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                data-testid="dashboard-new-project-button"
                onClick={() => nav('/projects/new')}
                className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-4 py-2 text-sm font-medium hover:bg-[hsl(var(--primary)/0.9)] transition-colors duration-150 shadow-[0_8px_24px_-12px_hsl(var(--primary)/0.7)]"
              >
                <Plus className="h-4 w-4" />
                New Project
              </button>
              <StatusBadge status="REAL" label="Honest acceptance" />
              <StatusBadge status="PLACEHOLDER" label="No template-only fallback" />
            </div>
          </div>
        </div>
      </div>

      {/* Projects */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <FolderGit2 className="h-4 w-4 text-muted-foreground" />
          <div className="text-sm font-semibold">Projects</div>
        </div>
        {error && (
          <div data-testid="error-alert" className="surface-1 p-4 flex items-center gap-3 text-sm border border-[hsl(var(--destructive)/0.35)]">
            <AlertCircle className="h-4 w-4 text-[hsl(var(--destructive))]" />
            <div>API offline. Check backend service.</div>
          </div>
        )}
        {!error && projects === null && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-xl" />
            ))}
          </div>
        )}
        {projects && projects.length === 0 && (
          <div className="surface-1 p-8 text-center">
            <div className="text-sm text-muted-foreground">No projects yet.</div>
            <button
              data-testid="dashboard-empty-new-project-button"
              onClick={() => nav('/projects/new')}
              className="mt-3 inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-4 py-2 text-sm font-medium"
            >
              <Plus className="h-4 w-4" /> Start a new project
            </button>
          </div>
        )}
        {projects && projects.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {projects.map(p => (
              <Link
                key={p.id}
                to={`/projects/${p.id}`}
                data-testid="project-card"
                className="surface-1 p-4 hover:bg-[hsl(var(--surface-2))] transition-colors duration-150 flex flex-col gap-3"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold truncate">{p.name}</div>
                    <div className="text-[11px] font-mono text-muted-foreground truncate">#{p.id}</div>
                  </div>
                  <StatePill state={p.state} />
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2">{p.idea}</p>
                <div className="flex flex-wrap gap-2 mt-auto">
                  {p.last_build_status && <StatusBadge status={p.last_build_status} label={`build ${p.last_build_status}`} />}
                  {p.last_acceptance_status && <StatusBadge status={p.last_acceptance_status} label={`accept ${p.last_acceptance_status}`} />}
                  {!p.last_build_status && !p.last_acceptance_status && <StatusBadge status="PLACEHOLDER" label="not yet built" />}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
