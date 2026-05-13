import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { AlertTriangle, Hammer, History, Wrench } from 'lucide-react';
import { toast } from 'sonner';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

const STUCK_STATES = new Set(['Generating', 'Building', 'Repair', 'Acceptance']);
const STUCK_GRACE_MS = 90_000;

export default function BuildPage() {
  const { project, refresh } = useOutletContext();
  const [builds, setBuilds] = useState([]);
  const [busy, setBusy] = useState(false);
  const [recovering, setRecovering] = useState(false);
  const [selected, setSelected] = useState(0);

  const load = async () => {
    const r = await api.listBuilds(project.id);
    setBuilds(r.builds || []);
  };
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); /* eslint-disable-next-line */ }, [project.id]);

  const trigger = async () => {
    try {
      setBusy(true);
      await api.triggerBuild(project.id);
      toast.success('Build started');
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed');
    } finally { setBusy(false); }
  };

  const onRecover = async () => {
    try {
      setRecovering(true);
      const out = await api.recoverProject(project.id);
      if (out.reason === 'no_op_not_stuck') {
        toast.info('Project is not stuck.');
      } else {
        toast.success(`Recovered: ${out.previous_state} -> ${out.recovered_state}. You can retry now.`);
      }
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Recover failed');
    } finally { setRecovering(false); }
  };

  // Detect orphaned pipeline: state is transient but no activity for >grace.
  const updatedAtMs = (project.updated_at || 0) * 1000;
  const isStuck = STUCK_STATES.has(project.state) && (Date.now() - updatedAtMs) > STUCK_GRACE_MS;

  const sel = builds[selected];

  return (
    <div className="flex flex-col gap-4">
      {isStuck && (
        <div
          className="surface-1 p-4 border border-[hsl(var(--warning))]/40 bg-[hsl(var(--warning))]/5 flex items-start justify-between gap-3 flex-wrap"
          data-testid="stuck-pipeline-banner"
        >
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 mt-0.5 text-[hsl(var(--warning))]" />
            <div className="text-xs">
              <div className="font-semibold">Pipeline appears stuck in <span className="font-mono">{project.state}</span></div>
              <div className="text-muted-foreground mt-0.5">
                No progress for over {Math.round((Date.now() - updatedAtMs) / 1000)}s. This usually means the backend
                restarted while the pipeline was running. Click <strong>Recover</strong> to reset
                state to the safest checkpoint, then retry.
              </div>
            </div>
          </div>
          <button
            onClick={onRecover}
            disabled={recovering}
            data-testid="recover-pipeline-button"
            className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--warning))] text-black px-3 py-1.5 text-xs font-medium hover:opacity-90 disabled:opacity-50"
          >
            {recovering ? 'Recovering…' : 'Recover'}
          </button>
        </div>
      )}

      <div className="surface-1 p-4 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Hammer className="h-4 w-4 text-[hsl(var(--warning))]" />
          <div className="text-sm font-semibold">Build runs & repairs</div>
        </div>
        <button
          onClick={trigger}
          disabled={busy}
          data-testid="run-build-button"
          className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-3 py-1.5 text-xs font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50"
        >Run build</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4">
        <div className="surface-1 overflow-hidden">
          <div className="border-b border-border px-3 py-2 text-[10px] uppercase tracking-wider text-muted-foreground font-mono flex items-center gap-1">
            <History className="h-3.5 w-3.5" /> History
          </div>
          <div className="max-h-[55vh] overflow-auto">
            {builds.length === 0 && <div className="p-3 text-xs text-muted-foreground italic">No build runs yet.</div>}
            {builds.map((b, i) => (
              <button
                key={i}
                data-testid="build-run-row"
                onClick={() => setSelected(i)}
                className={`w-full text-left px-3 py-2 border-b border-border flex items-center gap-2 ${selected === i ? 'bg-[hsl(var(--surface-2))]' : 'hover:bg-accent'}`}
              >
                <div className="flex-1">
                  <div className="text-xs font-mono">{new Date((b.created_at || 0) * 1000).toLocaleString()}</div>
                  <div className="text-[10px] text-muted-foreground">{(b.build?.summary?.duration_s || 0)}s · {b.repair?.attempts?.length || 0} repairs</div>
                </div>
                <StatusBadge status={b.build?.overall_status} />
              </button>
            ))}
          </div>
        </div>

        <div className="surface-1 overflow-hidden" data-testid="build-logs-panel">
          <div className="border-b border-border px-3 py-2 text-[10px] uppercase tracking-wider text-muted-foreground font-mono">Run detail</div>
          {!sel && <div className="p-3 text-xs text-muted-foreground italic">Select a run.</div>}
          {sel && (
            <div className="flex flex-col gap-3 p-3">
              <div className="flex flex-wrap gap-2">
                <StatusBadge status={sel.build?.overall_status} label={`overall ${sel.build?.overall_status}`} />
                <StatusBadge status={sel.build?.summary?.frontend_pass ? 'PASS' : 'FAIL'} label="frontend" />
                <StatusBadge status={sel.build?.summary?.backend_pass ? 'PASS' : 'FAIL'} label="backend" />
              </div>
              <div>
                <div className="text-xs font-semibold mb-1">Frontend steps</div>
                {(sel.build?.frontend || []).map((s, i) => (
                  <StepRow key={i} step={s} />
                ))}
              </div>
              <div>
                <div className="text-xs font-semibold mb-1">Backend steps</div>
                {(sel.build?.backend || []).map((s, i) => (
                  <StepRow key={i} step={s} />
                ))}
              </div>
              {sel.repair?.attempts?.length > 0 && (
                <div>
                  <div className="text-xs font-semibold mb-1 flex items-center gap-1"><Wrench className="h-3.5 w-3.5" /> Repair timeline</div>
                  <div className="flex flex-col gap-2">
                    {sel.repair.attempts.map((a, i) => (
                      <div key={i} data-testid="repair-attempt-node" className="rounded-md border border-border p-2 text-xs">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <div className="font-mono">attempt #{a.attempt}</div>
                          <StatusBadge status={a.build_after} />
                        </div>
                        <div className="text-[11px] text-muted-foreground">cls=<span className="font-mono text-foreground">{a.classification}</span> · file=<span className="font-mono">{a.target_file || '—'}</span> · step={a.target_step}</div>
                        <div className="text-[11px] text-muted-foreground mt-1">{a.note}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StepRow({ step }) {
  const ok = step.returncode === 0 && !step.skipped;
  return (
    <details className="rounded-md border border-border mb-1">
      <summary className="flex items-center justify-between gap-2 px-2 py-1.5 cursor-pointer">
        <div className="flex items-center gap-2 min-w-0">
          <StatusBadge status={step.skipped ? 'PLACEHOLDER' : (ok ? 'PASS' : 'FAIL')} />
          <span className="text-xs font-mono truncate">{step.name}</span>
        </div>
        <span className="text-[10px] text-muted-foreground font-mono">{step.duration_s?.toFixed?.(1) || 0}s</span>
      </summary>
      <pre className="text-[10px] font-mono p-2 bg-[hsl(var(--code-bg))] border-t border-border whitespace-pre-wrap break-all max-h-72 overflow-auto">
{`# cmd: ${(step.cmd || []).join(' ')}\n# stderr (tail)\n${step.stderr_tail || '(empty)'}\n# stdout (tail)\n${step.stdout_tail || '(empty)'}`}
      </pre>
    </details>
  );
}
