import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ListTree, Wand2, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

export default function PlanPage() {
  const { project, refresh } = useOutletContext();
  const [doc, setDoc] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const p = await api.getPlan(project.id);
    setDoc(p);
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [project.id]);

  const make = async () => {
    try {
      setBusy(true);
      await api.makePlan(project.id);
      toast.success('Plan generated');
      await load();
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed');
    } finally { setBusy(false); }
  };
  const run = async () => {
    try {
      setBusy(true);
      await api.runFullPipeline(project.id);
      toast.success('Generation pipeline started');
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed');
    } finally { setBusy(false); }
  };

  const plan = doc?.plan;
  return (
    <div className="flex flex-col gap-4">
      <div className="surface-1 p-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <ListTree className="h-4 w-4 text-[hsl(var(--primary))]" />
            <div className="text-sm font-semibold">File-level plan</div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={make}
              disabled={busy}
              data-testid="plan-generate-button"
              className="inline-flex items-center gap-2 rounded-md bg-secondary text-secondary-foreground border border-border px-3 py-1.5 text-xs font-medium hover:bg-accent disabled:opacity-50"
            >
              <Wand2 className="h-3.5 w-3.5" /> {plan ? 'Regenerate plan' : 'Generate plan'}
            </button>
            {plan && (
              <button
                onClick={run}
                disabled={busy}
                data-testid="plan-run-pipeline-button"
                className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-3 py-1.5 text-xs font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50"
              >
                Run pipeline <ArrowRight className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
      {!plan && <div className="text-xs text-muted-foreground italic">No plan yet. BRD + Architecture must be ready first.</div>}
      {plan && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="surface-1 p-4">
            <div className="text-sm font-semibold mb-1">{plan.app_name || project.name}</div>
            <p className="text-xs text-muted-foreground mb-3">{plan.summary}</p>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono mb-1">Files to generate ({(plan.files || []).length})</div>
            <div className="flex flex-col gap-1 max-h-[420px] overflow-auto code-surface p-2">
              {(plan.files || []).map((f, i) => {
                const path = typeof f === 'string' ? f : f.path;
                const purpose = typeof f === 'object' ? f.purpose : '';
                return (
                  <div key={i} className="flex items-center justify-between gap-2 text-[11px] font-mono px-2 py-1 hover:bg-[hsl(var(--surface-3))] rounded">
                    <span className="truncate">{path}</span>
                    <span className="text-muted-foreground truncate">{purpose}</span>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="flex flex-col gap-4">
            <div className="surface-1 p-4">
              <div className="text-sm font-semibold mb-2">Endpoints</div>
              <div className="flex flex-col gap-1 text-xs font-mono">
                {(plan.endpoints || []).map((e, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-[hsl(var(--surface-3))] text-[10px]">{e.method}</span>
                    <span>{e.path}</span>
                    <span className="text-muted-foreground truncate">— {e.purpose}</span>
                  </div>
                ))}
                {(plan.endpoints || []).length === 0 && <span className="text-muted-foreground italic text-xs">No endpoints listed.</span>}
              </div>
            </div>
            <div className="surface-1 p-4">
              <div className="text-sm font-semibold mb-2">Entities</div>
              <div className="flex flex-col gap-2 text-xs">
                {(plan.entities || []).map((ent, i) => (
                  <div key={i} className="rounded-md border border-border p-2">
                    <div className="font-medium">{ent.name}</div>
                    <div className="text-[11px] font-mono text-muted-foreground">
                      {(ent.fields || []).map(f => `${f.name}:${f.type}`).join(', ')}
                    </div>
                  </div>
                ))}
                {(plan.entities || []).length === 0 && <span className="text-muted-foreground italic">No entities listed.</span>}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
