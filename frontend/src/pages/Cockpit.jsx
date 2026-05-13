import React, { useEffect, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { Play, ArrowRight, ListTree, Network, MessagesSquare, FileCode2, Hammer, ClipboardCheck, Package } from 'lucide-react';
import { toast } from 'sonner';
import StatusBadge from '@/components/cockpit/StatusBadge';
import PhaseStepper from '@/components/cockpit/PhaseStepper';
import api from '@/lib/api';
import useEventStream from '@/lib/useEventStream';

function QuickStat({ label, value, status, testid }) {
  return (
    <div className="surface-1 p-4 min-w-0" data-testid={testid}>
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">{label}</div>
      <div className="flex items-center gap-2 mt-1">
        <div className="text-sm font-semibold truncate">{value || '—'}</div>
        {status && <StatusBadge status={status} />}
      </div>
    </div>
  );
}

export default function Cockpit() {
  const { project, refresh } = useOutletContext();
  const [running, setRunning] = useState(false);
  const [pipelineRunning, setPipelineRunning] = useState(false);

  const { events: live } = useEventStream(api.eventsStreamUrl(project.id), { enabled: !!project?.id });

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const s = await api.generateStatus(project.id);
        if (alive) setPipelineRunning(!!s.running);
      } catch (_) { /* ignore */ }
    };
    poll();
    const t = setInterval(poll, 3000);
    return () => { alive = false; clearInterval(t); };
  }, [project.id]);

  const triggerFull = async () => {
    try {
      setRunning(true);
      await api.runFullPipeline(project.id);
      toast.success('Pipeline started: architecture → plan → generate → build → repair → acceptance → export');
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to start');
    } finally {
      setRunning(false);
      refresh();
    }
  };

  const hasBrd = (project.brd_maturity || 0) > 0;
  const pipelineDisabled = running || pipelineRunning || !hasBrd;
  const pipelineLabel = !hasBrd
    ? 'Answer BRD first'
    : pipelineRunning
      ? 'Pipeline running…'
      : 'Run full pipeline';

  const links = [
    { to: `/projects/${project.id}/brd`, label: 'BRD intake', icon: MessagesSquare, desc: 'SME-style questions + structured requirements' },
    { to: `/projects/${project.id}/architecture`, label: 'Architecture', icon: Network, desc: 'Classification + reasoning + override' },
    { to: `/projects/${project.id}/plan`, label: 'Plan', icon: ListTree, desc: 'File-level plan + endpoints + entities' },
    { to: `/projects/${project.id}/files`, label: 'Files', icon: FileCode2, desc: 'Generated code tree + viewer' },
    { to: `/projects/${project.id}/build`, label: 'Build & Repair', icon: Hammer, desc: 'Real npm + pip build with repair budget' },
    { to: `/projects/${project.id}/acceptance`, label: 'Acceptance', icon: ClipboardCheck, desc: 'Honest PASS/PARTIAL/FAIL per check' },
    { to: `/projects/${project.id}/export`, label: 'Export', icon: Package, desc: 'Clean ZIP + manifest + secret scan' },
  ];

  return (
    <div className="flex flex-col gap-6">
      <PhaseStepper currentState={project.state} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <QuickStat label="BRD maturity" value={`${project.brd_maturity || 0}/100`} testid="cockpit-stat-brd" />
        <QuickStat label="Last build" value={project.last_build_status || 'not run'} status={project.last_build_status} testid="cockpit-stat-build" />
        <QuickStat label="Acceptance" value={project.last_acceptance_status || 'not run'} status={project.last_acceptance_status} testid="cockpit-stat-acceptance" />
        <QuickStat label="Export" value={project.last_export_path ? 'available' : 'not yet'} status={project.last_export_path ? 'REAL' : 'PLACEHOLDER'} testid="cockpit-stat-export" />
      </div>

      <div className="surface-1 p-5">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <div className="text-sm font-semibold">Run full pipeline</div>
            <p className="text-xs text-muted-foreground mt-1 max-w-xl">
              One click runs: architecture detection → plan → generate code → build (npm + pip) →
              safe repair (max 2 retries) → acceptance checks → auto-export on PASS/PARTIAL.
              You do not need 100% BRD maturity — even a few answers are enough to start.
            </p>
          </div>
          <button
            onClick={triggerFull}
            disabled={pipelineDisabled}
            data-testid="run-pipeline-button"
            className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-4 py-2 text-sm font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50 shadow-[0_8px_24px_-12px_hsl(var(--primary)/0.7)]"
          >
            <Play className="h-4 w-4" /> {pipelineLabel}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {links.map(l => (
          <Link key={l.to} to={l.to} className="surface-1 p-4 hover:bg-[hsl(var(--surface-2))] transition-colors duration-150 flex items-start gap-3 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[hsl(var(--primary)/0.10)] border border-[hsl(var(--primary)/0.25)]">
              <l.icon className="h-4 w-4 text-[hsl(var(--primary))]" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold">{l.label}</div>
              <div className="text-xs text-muted-foreground">{l.desc}</div>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground self-center group-hover:translate-x-0.5 transition-transform" />
          </Link>
        ))}
      </div>

      <div className="surface-1 p-4" data-testid="cockpit-mini-event-feed">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm font-semibold">Recent activity</div>
          <div className="text-[10px] font-mono text-muted-foreground">live</div>
        </div>
        <div className="flex flex-col gap-1.5">
          {(live || []).slice(0, 8).map((e, i) => (
            <div key={(e.id || '') + i} className="flex items-center gap-2 text-xs">
              <span className="font-mono text-[10px] text-muted-foreground w-16 shrink-0">{new Date((e.created_at || 0) * 1000).toLocaleTimeString().slice(0, 8)}</span>
              <span className="font-medium truncate">{e.type}</span>
              <span className="text-muted-foreground truncate">{e.message}</span>
            </div>
          ))}
          {(live || []).length === 0 && (
            <div className="text-xs text-muted-foreground italic">No events yet — trigger a pipeline above.</div>
          )}
        </div>
      </div>
    </div>
  );
}
