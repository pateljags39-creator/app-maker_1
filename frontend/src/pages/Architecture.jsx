import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Network, Compass, ShieldAlert } from 'lucide-react';
import { toast } from 'sonner';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

const KINDS = ['frontend_only', 'api_driven', 'db_backed', 'backend_required', 'full_stack'];

export default function ArchitecturePage() {
  const { project, refresh } = useOutletContext();
  const [doc, setDoc] = useState(null);
  const [busy, setBusy] = useState(false);
  const [forced, setForced] = useState('');
  const [allowLimited, setAllowLimited] = useState(false);

  const load = async () => {
    const a = await api.getArchitecture(project.id);
    setDoc(a);
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [project.id]);

  const detect = async () => {
    try {
      setBusy(true);
      await api.detectArchitecture(project.id);
      toast.success('Architecture detected');
      await load();
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Detect failed');
    } finally { setBusy(false); }
  };
  const override = async () => {
    try {
      setBusy(true);
      await api.overrideArchitecture(project.id, { forced_architecture: forced || null, allow_limited_prototype: !!allowLimited });
      toast.success('Override applied');
      await load();
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Override failed');
    } finally { setBusy(false); }
  };

  const decision = doc?.decision;
  return (
    <div className="flex flex-col gap-4">
      <div className="surface-1 p-5">
        <div className="flex items-center justify-between flex-wrap gap-3 mb-3">
          <div className="flex items-center gap-2">
            <Network className="h-4 w-4 text-[hsl(var(--primary))]" />
            <div className="text-sm font-semibold">Architecture decision</div>
          </div>
          <button
            onClick={detect}
            disabled={busy}
            data-testid="architecture-detect-button"
            className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-3 py-1.5 text-xs font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50"
          >
            <Compass className="h-3.5 w-3.5" /> Detect from BRD
          </button>
        </div>

        {!decision && (
          <div className="text-xs text-muted-foreground italic">No architecture detected yet. Click “Detect from BRD” after submitting some BRD answers.</div>
        )}
        {decision && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs rounded-md bg-[hsl(var(--code-bg))] border border-[hsl(var(--code-border))] px-2 py-1">kind: <strong className="text-[hsl(var(--primary))]">{decision.kind}</strong></span>
              <StatusBadge status={decision.requires_backend ? 'REAL' : 'PLACEHOLDER'} label={`backend: ${decision.requires_backend}`} />
              <StatusBadge status={decision.requires_database ? 'REAL' : 'PLACEHOLDER'} label={`db: ${decision.requires_database}`} />
              {decision.blocked && <StatusBadge status="BLOCKED" label="blocked" />}
              {decision.limited_prototype_accepted && <StatusBadge status="WARN" label="limited prototype accepted" />}
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono mb-1">Reasoning</div>
              <ul className="text-xs space-y-1">
                {(decision.reasoning || []).map((r, i) => (
                  <li key={i} className="text-muted-foreground">• {r}</li>
                ))}
              </ul>
            </div>
            {decision.blocked && (
              <div className="rounded-md border border-[hsl(var(--blocked)/0.35)] bg-[hsl(var(--blocked)/0.10)] p-3 text-xs">
                <div className="flex items-center gap-2 mb-1">
                  <ShieldAlert className="h-3.5 w-3.5 text-[hsl(var(--blocked))]" />
                  <div className="font-semibold">Blocked combination</div>
                </div>
                <ul className="list-disc list-inside text-muted-foreground space-y-0.5">
                  {(decision.block_reasons || []).map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="surface-1 p-5">
        <div className="text-sm font-semibold mb-2">Override (advanced)</div>
        <p className="text-xs text-muted-foreground mb-3 max-w-xl">
          Force a specific architecture. If your forced kind conflicts with BRD requirements, the
          system blocks generation unless you explicitly opt into “limited prototype” (acknowledging
          it will not deliver the full BRD).
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] text-muted-foreground">Force kind</span>
            <select
              data-testid="architecture-override-select"
              value={forced}
              onChange={e => setForced(e.target.value)}
              className="rounded-md border border-border bg-secondary text-sm px-2 py-1.5"
            >
              <option value="">(use detection)</option>
              {KINDS.map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              data-testid="architecture-limited-prototype-checkbox"
              type="checkbox"
              checked={allowLimited}
              onChange={e => setAllowLimited(e.target.checked)}
            />
            <span className="text-muted-foreground">Accept limited prototype</span>
          </label>
          <button
            onClick={override}
            disabled={busy}
            data-testid="architecture-override-apply-button"
            className="inline-flex items-center gap-2 rounded-md bg-secondary text-secondary-foreground border border-border px-3 py-1.5 text-xs font-medium hover:bg-accent disabled:opacity-50"
          >Apply override</button>
        </div>
      </div>
    </div>
  );
}
