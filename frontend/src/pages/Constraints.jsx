import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Shield, RotateCcw, Save, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

const AREAS = [
  { id: 'frontend', label: 'Frontend (frontend/*)' },
  { id: 'backend',  label: 'Backend (backend/*)' },
  { id: 'root',     label: 'Top-level (README, .gitignore, etc.)' },
];

export default function Constraints() {
  const { project } = useOutletContext();
  const [c, setC] = useState(null);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [err, setErr] = useState(null);

  const load = async () => {
    try {
      const data = await api.getConstraints(project.id);
      setC(data.constraints);
      setErr(null);
    } catch (e) {
      setErr(e?.message || 'failed');
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [project.id]);

  const upd = (k, v) => setC(prev => ({ ...prev, [k]: v }));
  const toggleArea = (id) => setC(prev => {
    const cur = new Set(prev.allowed_areas || []);
    if (cur.has(id)) cur.delete(id); else cur.add(id);
    return { ...prev, allowed_areas: Array.from(cur) };
  });

  const save = async () => {
    setSaving(true);
    try {
      const data = await api.putConstraints(project.id, c);
      setC(data.constraints);
      toast.success('Constraints saved');
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const reset = async () => {
    setResetting(true);
    try {
      const data = await api.resetConstraints(project.id);
      setC(data.constraints);
      toast.success('Reset to defaults');
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to reset');
    } finally {
      setResetting(false);
    }
  };

  if (err) return <div className="surface-1 p-4 text-sm text-[hsl(var(--destructive))]">Failed to load: {err}</div>;
  if (!c) return <div className="surface-1 p-8 text-sm text-muted-foreground">Loading constraints…</div>;

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      <div className="surface-1 p-6 flex items-start gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[hsl(var(--primary)/0.18)] border border-[hsl(var(--primary)/0.35)] shrink-0">
          <Shield className="h-5 w-5 text-[hsl(var(--primary))]" />
        </div>
        <div>
          <div className="text-lg font-semibold">Bounded customization constraints</div>
          <p className="text-xs text-muted-foreground mt-1 max-w-xl">
            These limits scope every Improve/Fix and Repair attempt. Hard rules (no
            secrets, no .env/.factory/.git edits, no writes outside workspace) are
            always enforced and cannot be turned off.
          </p>
        </div>
      </div>

      <div className="surface-1 p-5">
        <div className="text-sm font-semibold mb-3">Change budget</div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <NumberField label="Max files changed" value={c.max_files_changed} onChange={(v) => upd('max_files_changed', v)} min={1} max={50} testid="constraint-max-files" />
          <NumberField label="Max new files" value={c.max_new_files} onChange={(v) => upd('max_new_files', v)} min={0} max={30} testid="constraint-max-new-files" />
          <NumberField label="Max total LOC changed" value={c.max_total_loc_changed} onChange={(v) => upd('max_total_loc_changed', v)} min={50} max={20000} testid="constraint-max-loc" />
        </div>
      </div>

      <div className="surface-1 p-5">
        <div className="text-sm font-semibold mb-1">Scope</div>
        <div className="text-xs text-muted-foreground mb-3">Which areas of the project can be edited.</div>
        <div className="flex flex-col gap-1.5">
          {AREAS.map(a => (
            <label key={a.id} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={(c.allowed_areas || []).includes(a.id)}
                onChange={() => toggleArea(a.id)}
                data-testid={`constraint-area-${a.id}`}
              />
              <span>{a.label}</span>
            </label>
          ))}
        </div>
        <label className="flex items-center gap-2 text-sm mt-3">
          <input type="checkbox" checked={!!c.no_new_top_level_dirs}
                 onChange={(e) => upd('no_new_top_level_dirs', e.target.checked)}
                 data-testid="constraint-no-new-top-dirs" />
          <span>Disallow new top-level directories</span>
        </label>
      </div>

      <div className="surface-1 p-5">
        <div className="text-sm font-semibold mb-3">Dependencies</div>
        <div className="flex flex-col gap-2 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={!!c.allow_npm_deps_changes}
                   onChange={(e) => upd('allow_npm_deps_changes', e.target.checked)}
                   data-testid="constraint-allow-npm" />
            <span>Allow npm dependency additions</span>
          </label>
          <NumberField label="Max new npm deps" value={c.max_new_npm_deps} onChange={(v) => upd('max_new_npm_deps', v)} min={0} max={30} testid="constraint-max-npm" />
          <label className="flex items-center gap-2 mt-2">
            <input type="checkbox" checked={!!c.allow_pip_deps_changes}
                   onChange={(e) => upd('allow_pip_deps_changes', e.target.checked)}
                   data-testid="constraint-allow-pip" />
            <span>Allow pip dependency additions</span>
          </label>
          <NumberField label="Max new pip deps" value={c.max_new_pip_deps} onChange={(v) => upd('max_new_pip_deps', v)} min={0} max={30} testid="constraint-max-pip" />
        </div>
      </div>

      <div className="surface-1 p-5">
        <div className="text-sm font-semibold mb-2">Notes (optional)</div>
        <textarea
          className="w-full bg-background border border-border rounded-md p-2 text-sm font-mono"
          rows={3}
          value={c.notes || ''}
          onChange={(e) => upd('notes', e.target.value)}
          placeholder="Free-form context the AI should consider with every change…"
          data-testid="constraint-notes"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <button onClick={save} disabled={saving}
                data-testid="save-constraints-button"
                className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-4 py-2 text-sm font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50">
          <Save className="h-4 w-4" /> {saving ? 'Saving…' : 'Save constraints'}
        </button>
        <button onClick={reset} disabled={resetting}
                data-testid="reset-constraints-button"
                className="inline-flex items-center gap-2 rounded-md border border-border bg-secondary px-4 py-2 text-sm hover:bg-accent disabled:opacity-50">
          <RotateCcw className="h-4 w-4" /> {resetting ? 'Resetting…' : 'Reset to defaults'}
        </button>
      </div>

      <div className="surface-1 p-4 flex items-start gap-3 border border-[hsl(var(--primary)/0.25)]">
        <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5" />
        <div className="text-xs text-muted-foreground">
          Hard rules (always-on): no edits to <code>.env*</code>, <code>.factory</code>, <code>node_modules</code>,
          <code>dist</code>, <code>build</code>, <code>.git</code>; no secrets in any file content; no path
          escapes outside the project workspace.
        </div>
      </div>
    </div>
  );
}

function NumberField({ label, value, onChange, min, max, testid }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">{label}</span>
      <input
        type="number"
        className="bg-background border border-border rounded-md px-2 py-1.5 text-sm"
        value={value ?? 0}
        min={min} max={max}
        onChange={(e) => onChange(Math.max(min ?? 0, Math.min(max ?? 999999, Number(e.target.value) || 0)))}
        data-testid={testid}
      />
    </label>
  );
}
