import React, { useEffect, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { Wand2, Shield, ChevronRight, FileText, AlertTriangle, CheckCircle2, RotateCcw, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

const STATUS_META = {
  applied:                  { icon: CheckCircle2, color: 'text-emerald-400', label: 'Applied', badge: 'PASS' },
  rolled_back:              { icon: RotateCcw,    color: 'text-amber-400',   label: 'Rolled back', badge: 'PARTIAL' },
  rejected_by_constraints:  { icon: Shield,       color: 'text-amber-400',   label: 'Rejected by constraints', badge: 'PARTIAL' },
  llm_failed:               { icon: XCircle,      color: 'text-red-400',     label: 'LLM failed', badge: 'FAIL' },
  pending:                  { icon: Wand2,        color: 'text-muted-foreground', label: 'Pending', badge: 'PLACEHOLDER' },
};

export default function Improve() {
  const { project, refresh } = useOutletContext();
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [attempts, setAttempts] = useState(null);
  const [constraints, setConstraints] = useState(null);
  const [openId, setOpenId] = useState(null);

  const load = async () => {
    try {
      const [list, c] = await Promise.all([
        api.listImproves(project.id),
        api.getConstraints(project.id),
      ]);
      setAttempts(list || []);
      setConstraints(c.constraints);
    } catch (e) {
      console.warn('Improve load failed', e);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [project.id]);

  const submit = async () => {
    if (!text.trim() || text.trim().length < 4) {
      toast.error('Describe the change in at least a sentence');
      return;
    }
    setSubmitting(true);
    try {
      const rec = await api.requestImprove(project.id, text.trim());
      toast.success(`Improve attempt ${rec.attempt?.id || ''} — ${rec.attempt?.status || 'done'}`);
      setText('');
      await load();
      refresh?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Improve failed');
    } finally {
      setSubmitting(false);
    }
  };

  const blocked = !(project?.last_acceptance_status || project?.last_build_status);

  return (
    <div className="flex flex-col gap-6">
      <div className="surface-1 p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[hsl(var(--primary)/0.18)] border border-[hsl(var(--primary)/0.35)] shrink-0">
            <Wand2 className="h-5 w-5 text-[hsl(var(--primary))]" />
          </div>
          <div className="flex-1">
            <div className="text-lg font-semibold">Improve / Fix</div>
            <p className="text-xs text-muted-foreground mt-1 max-w-2xl">
              Request a <strong>bounded</strong> change on the existing generated project. The AI proposes a
              change manifest, we validate it against your{' '}
              <Link to={`/projects/${project.id}/constraints`} className="text-[hsl(var(--link))] underline">constraints</Link>,
              apply it, rebuild, and roll back automatically on any regression.
            </p>
          </div>
        </div>

        {constraints && (
          <div className="mt-4 flex flex-wrap gap-2 text-[11px] font-mono text-muted-foreground" data-testid="improve-constraints-pills">
            <Pill>max {constraints.max_files_changed} files</Pill>
            <Pill>max {constraints.max_new_files} new</Pill>
            <Pill>~{constraints.max_total_loc_changed} LOC</Pill>
            <Pill>areas: {(constraints.allowed_areas || []).join(', ')}</Pill>
            {!constraints.allow_npm_deps_changes && <Pill>no npm deps</Pill>}
            {!constraints.allow_pip_deps_changes && <Pill>no pip deps</Pill>}
            {constraints.no_new_top_level_dirs && <Pill>no new top dirs</Pill>}
          </div>
        )}

        {blocked && (
          <div className="mt-4 flex items-start gap-2 text-xs text-amber-300">
            <AlertTriangle className="h-4 w-4" />
            <div>This project has not been built yet. Generate it from the Cockpit first; Improve operates on existing code.</div>
          </div>
        )}

        <textarea
          className="mt-4 w-full bg-background border border-border rounded-md p-3 text-sm font-mono"
          rows={4}
          placeholder="e.g., Add an /api/notes/search endpoint that filters by title (case-insensitive) and wire a search input on the notes list page."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={submitting || blocked}
          data-testid="improve-change-request-textarea"
        />
        <div className="mt-3 flex items-center gap-2">
          <button
            onClick={submit}
            disabled={submitting || blocked || text.trim().length < 4}
            data-testid="improve-submit-button"
            className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-4 py-2 text-sm font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50"
          >
            <Wand2 className="h-4 w-4" />
            {submitting ? 'Running… (1 Pro call + build)' : 'Request improvement'}
          </button>
          <Link to={`/projects/${project.id}/constraints`} className="text-xs text-[hsl(var(--link))]">Edit constraints →</Link>
        </div>
      </div>

      <section>
        <div className="flex items-center gap-2 mb-3">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <div className="text-sm font-semibold">Past improve attempts</div>
        </div>
        {attempts === null && <div className="surface-1 p-6 text-sm text-muted-foreground">Loading…</div>}
        {attempts && attempts.length === 0 && (
          <div className="surface-1 p-6 text-sm text-muted-foreground">No improve attempts yet for this project.</div>
        )}
        {attempts && attempts.length > 0 && (
          <div className="flex flex-col gap-2">
            {attempts.map(rec => {
              const a = rec.attempt || rec;
              const meta = STATUS_META[a.status] || STATUS_META.pending;
              const Icon = meta.icon;
              const open = openId === a.id;
              return (
                <div key={a.id} className="surface-1 p-3" data-testid="improve-attempt-card">
                  <button className="w-full text-left flex items-start gap-3" onClick={() => setOpenId(open ? null : a.id)}>
                    <Icon className={`h-4 w-4 mt-1 ${meta.color}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <div className="text-sm font-medium truncate">{a.summary || a.change_request?.slice(0, 80) || a.id}</div>
                        <StatusBadge status={meta.badge} label={meta.label} />
                        {a.build_after && <StatusBadge status={a.build_after} label={`build ${a.build_after}`} />}
                        {a.acceptance_after && <StatusBadge status={a.acceptance_after} label={`accept ${a.acceptance_after}`} />}
                      </div>
                      <div className="text-[11px] font-mono text-muted-foreground mt-0.5">
                        #{a.id} · {(a.files_changed || []).length} file{(a.files_changed || []).length === 1 ? '' : 's'} · {a.violations?.length || 0} violation{(a.violations?.length || 0) === 1 ? '' : 's'}
                      </div>
                    </div>
                    <ChevronRight className={`h-4 w-4 mt-1 text-muted-foreground transition-transform ${open ? 'rotate-90' : ''}`} />
                  </button>
                  {open && (
                    <div className="mt-3 ml-7 flex flex-col gap-2 text-xs">
                      {a.change_request && (
                        <div><span className="text-muted-foreground">Request: </span><span className="font-mono">{a.change_request}</span></div>
                      )}
                      {a.rationale && <div><span className="text-muted-foreground">Rationale: </span>{a.rationale}</div>}
                      {(a.violations || []).length > 0 && (
                        <div className="text-amber-300">
                          <div className="font-semibold mb-1">Violations:</div>
                          <ul className="list-disc pl-5">
                            {a.violations.map((v, i) => <li key={i} className="font-mono">{v}</li>)}
                          </ul>
                        </div>
                      )}
                      {(a.files_changed || []).length > 0 && (
                        <div>
                          <div className="text-muted-foreground font-semibold mb-1">Files:</div>
                          <ul className="font-mono">
                            {a.files_changed.map(f => (
                              <li key={f.path}>
                                <span className={
                                  f.action === 'create' ? 'text-emerald-400'
                                  : f.action === 'delete' ? 'text-red-400'
                                  : 'text-amber-300'
                                }>{f.action}</span>{' '}{f.path}{' '}
                                <span className="text-muted-foreground">({f.before_lines || 0} → {f.after_lines || 0} lines)</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {(a.add_npm_deps || []).length > 0 && (
                        <div className="font-mono">+npm: {(a.add_npm_deps || []).map(d => `${d.name}@${d.version}`).join(', ')}</div>
                      )}
                      {(a.add_pip_deps || []).length > 0 && (
                        <div className="font-mono">+pip: {(a.add_pip_deps || []).join(', ')}</div>
                      )}
                      {(a.unsupported || []).length > 0 && (
                        <div>
                          <div className="text-muted-foreground font-semibold mb-1">Unsupported (left out):</div>
                          <ul className="list-disc pl-5">
                            {a.unsupported.map((u, i) => <li key={i}>{u}</li>)}
                          </ul>
                        </div>
                      )}
                      {a.error && <div className="text-red-400 font-mono">{a.error}</div>}
                      {a.rolled_back && <div className="text-amber-300">Rolled back to snapshot {a.snapshot_before}.</div>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function Pill({ children }) {
  return <span className="px-2 py-0.5 rounded-full bg-[hsl(var(--surface-2))] border border-border">{children}</span>;
}
