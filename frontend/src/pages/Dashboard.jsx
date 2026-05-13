import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Activity, FolderGit2, AlertCircle, AlertTriangle, Sparkles, Search } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import StatePill from '@/components/cockpit/StatePill';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

const STUCK_STATES = new Set(['Generating', 'Building', 'Repair', 'Acceptance']);
const STUCK_GRACE_MS = 90_000;
const isStuck = (p) => STUCK_STATES.has(p.state) && (Date.now() - (p.updated_at || 0) * 1000) > STUCK_GRACE_MS;

export default function Dashboard() {
  const [projects, setProjects] = useState(null);
  const [error, setError] = useState(null);
  const [sandboxOpen, setSandboxOpen] = useState(false);
  const [filter, setFilter] = useState('');
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
              <button
                data-testid="dashboard-open-sandbox-button"
                onClick={() => setSandboxOpen(true)}
                className="inline-flex items-center gap-2 rounded-md border border-[hsl(var(--primary)/0.45)] bg-[hsl(var(--primary)/0.10)] text-foreground px-4 py-2 text-sm font-medium hover:bg-[hsl(var(--primary)/0.18)] transition-colors duration-150"
              >
                <Sparkles className="h-4 w-4 text-[hsl(var(--primary))]" />
                Run Sandbox
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
                  {isStuck(p) && (
                    <span
                      data-testid="project-stuck-badge"
                      className="inline-flex items-center gap-1 rounded-md border border-[hsl(var(--warning))]/40 bg-[hsl(var(--warning))]/10 px-2 py-0.5 text-[10px] font-medium text-[hsl(var(--warning))]"
                      title={`Stuck in ${p.state} — open the project & click Recover.`}
                    >
                      <AlertTriangle className="h-3 w-3" /> stuck · recover
                    </span>
                  )}
                  {p.last_build_status && <StatusBadge status={p.last_build_status} label={`build ${p.last_build_status}`} />}
                  {p.last_acceptance_status && <StatusBadge status={p.last_acceptance_status} label={`accept ${p.last_acceptance_status}`} />}
                  {!p.last_build_status && !p.last_acceptance_status && !isStuck(p) && <StatusBadge status="PLACEHOLDER" label="not yet built" />}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Sandbox project picker modal */}
      <Dialog open={sandboxOpen} onOpenChange={setSandboxOpen}>
        <DialogContent
          data-testid="sandbox-picker-modal"
          className="sm:max-w-[560px] bg-card border-border"
        >
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-[hsl(var(--primary))]" />
              Run Sandbox
            </DialogTitle>
            <DialogDescription className="text-xs">
              Pick a project to launch in the live sandbox. The app boots inside an iframe — frontend + backend, on your machine.
            </DialogDescription>
          </DialogHeader>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              data-testid="sandbox-picker-search"
              autoFocus
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Filter projects…"
              className="w-full rounded-md border border-border bg-background pl-8 pr-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--primary)/0.35)]"
            />
          </div>
          <div className="max-h-[360px] overflow-y-auto flex flex-col gap-1.5 mt-1">
            {(projects || [])
              .filter((p) => {
                const q = filter.trim().toLowerCase();
                if (!q) return true;
                return [p.name, p.id, p.idea].filter(Boolean).some((s) => s.toLowerCase().includes(q));
              })
              .map((p) => (
                <button
                  key={p.id}
                  data-testid={`sandbox-picker-row-${p.id}`}
                  onClick={() => { setSandboxOpen(false); nav(`/projects/${p.id}/sandbox`); }}
                  className="flex items-center gap-3 rounded-md border border-border bg-background hover:bg-[hsl(var(--surface-2))] px-3 py-2 text-left transition-colors"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[hsl(var(--primary)/0.10)] border border-[hsl(var(--primary)/0.25)] shrink-0">
                    <Sparkles className="h-3.5 w-3.5 text-[hsl(var(--primary))]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{p.name}</div>
                    <div className="text-[11px] font-mono text-muted-foreground truncate">#{p.id}</div>
                  </div>
                  <StatePill state={p.state} />
                </button>
              ))}
            {projects && projects.length === 0 && (
              <div className="text-xs text-muted-foreground italic px-2 py-3">
                No projects yet — create one first.
              </div>
            )}
            {projects && projects.length > 0 && projects.filter((p) => {
              const q = filter.trim().toLowerCase();
              return !q || [p.name, p.id, p.idea].filter(Boolean).some((s) => s.toLowerCase().includes(q));
            }).length === 0 && (
              <div className="text-xs text-muted-foreground italic px-2 py-3">
                No projects match “{filter}”.
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
