import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ClipboardCheck, Play } from 'lucide-react';
import { toast } from 'sonner';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

export default function AcceptancePage() {
  const { project, refresh } = useOutletContext();
  const [doc, setDoc] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const r = await api.latestAcceptance(project.id);
    setDoc(r);
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [project.id]);

  const run = async () => {
    try {
      setBusy(true);
      await api.runAcceptance(project.id);
      toast.success('Acceptance run complete');
      await load();
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed');
    } finally { setBusy(false); }
  };

  const report = doc?.report;
  return (
    <div className="flex flex-col gap-4">
      <div className="surface-1 p-4 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <ClipboardCheck className="h-4 w-4 text-[hsl(var(--success))]" />
          <div className="text-sm font-semibold">Acceptance checks</div>
        </div>
        <button onClick={run} disabled={busy} data-testid="run-acceptance-button" className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-3 py-1.5 text-xs font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50">
          <Play className="h-3.5 w-3.5" /> Run acceptance
        </button>
      </div>
      {!report && <div className="text-xs text-muted-foreground italic">No acceptance report yet.</div>}
      {report && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="surface-1 p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-semibold">Checks ({report.checks?.length || 0})</div>
              <StatusBadge status={report.overall} label={`overall ${report.overall}`} />
            </div>
            <table data-testid="acceptance-matrix-table" className="w-full text-xs">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">
                  <th className="text-left py-1">Check</th><th className="text-left py-1">Status</th><th className="text-left py-1">Detail</th>
                </tr>
              </thead>
              <tbody>
                {(report.checks || []).map((c, i) => (
                  <tr data-testid="acceptance-matrix-cell" key={i} className="border-t border-border">
                    <td className="py-1 pr-2 font-mono align-top">{c.name}</td>
                    <td className="py-1 pr-2 align-top"><StatusBadge status={c.status} /></td>
                    <td className="py-1 text-muted-foreground align-top">{c.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="surface-1 p-4">
            <div className="text-sm font-semibold mb-2">Requirement coverage</div>
            <div className="flex flex-col gap-2 max-h-[60vh] overflow-auto">
              {(report.requirement_coverage || []).map((rc, i) => (
                <div key={i} className="rounded-md border border-border p-2 text-xs">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="text-xs">{rc.requirement}</div>
                    <StatusBadge status={rc.status} />
                  </div>
                  {rc.matched_files?.length > 0 && (
                    <div className="text-[10px] font-mono text-muted-foreground">matched: {rc.matched_files.slice(0, 4).join(', ')}{rc.matched_files.length > 4 ? '…' : ''}</div>
                  )}
                </div>
              ))}
              {(report.requirement_coverage || []).length === 0 && (
                <div className="text-xs text-muted-foreground italic">No requirement coverage data.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
