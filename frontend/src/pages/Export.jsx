import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Package, DownloadCloud, FileText, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

export default function ExportPage() {
  const { project, refresh } = useOutletContext();
  const [doc, setDoc] = useState(null);
  const [manifest, setManifest] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const r = await api.latestExport(project.id);
    setDoc(r);
    try {
      const m = await api.exportManifest(project.id);
      setManifest(m);
    } catch { setManifest(null); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [project.id]);

  const exportNow = async () => {
    try {
      setBusy(true);
      await api.makeExport(project.id);
      toast.success('Export created');
      await load();
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed');
    } finally { setBusy(false); }
  };

  const exp = doc?.export;
  return (
    <div className="flex flex-col gap-4">
      <div className="surface-1 p-4 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Package className="h-4 w-4 text-[hsl(var(--primary))]" />
          <div className="text-sm font-semibold">Export ZIP</div>
        </div>
        <div className="flex items-center gap-2">
          <button
            data-testid="export-zip-button"
            onClick={exportNow}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-3 py-1.5 text-xs font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50"
          >
            <Package className="h-3.5 w-3.5" /> Create export
          </button>
          {exp && (
            <a
              href={api.exportDownloadUrl(project.id)}
              data-testid="export-download-link"
              className="inline-flex items-center gap-2 rounded-md bg-secondary border border-border text-secondary-foreground px-3 py-1.5 text-xs font-medium hover:bg-accent"
              download
            ><DownloadCloud className="h-3.5 w-3.5" /> Download ZIP</a>
          )}
        </div>
      </div>
      {!exp && <div className="text-xs text-muted-foreground italic">No export yet.</div>}
      {exp && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="surface-1 p-4">
            <div className="text-sm font-semibold mb-2">Last export</div>
            <div className="text-xs font-mono break-all">{exp.path}</div>
            <div className="mt-3 flex flex-wrap gap-2">
              <StatusBadge status={exp.secret_findings === 0 ? 'PASS' : 'FAIL'} label={exp.secret_findings === 0 ? 'no secrets' : `${exp.secret_findings} secret findings`} />
              <StatusBadge status="REAL" label={`${exp.files} files`} />
              <StatusBadge status="REAL" label={`${(exp.size_bytes / 1024).toFixed(1)} KB`} />
            </div>
            <div className="mt-2 text-[10px] font-mono text-muted-foreground break-all">sha256: {exp.sha256}</div>
          </div>
          <div className="surface-1 p-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <div className="text-sm font-semibold">Manifest</div>
            </div>
            {!manifest && <div className="text-xs text-muted-foreground italic">Manifest not available.</div>}
            {manifest && (
              <div className="flex flex-col gap-2 text-xs">
                <div className="flex flex-wrap gap-2">
                  <StatusBadge status="REAL" label={`${manifest.file_count} files included`} />
                  <StatusBadge status="REAL" label={`${manifest.size_bytes} bytes`} />
                  <StatusBadge status="PLACEHOLDER" label={`${manifest.excluded_dirs.length} dir patterns excluded`} />
                </div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono mt-2">Excluded</div>
                <div className="flex flex-wrap gap-1">
                  {manifest.excluded_dirs.map((d) => (
                    <code key={d} className="text-[10px] px-1.5 py-0.5 rounded bg-[hsl(var(--surface-3))]">{d}</code>
                  ))}
                </div>
                {manifest.secret_findings?.length > 0 && (
                  <div className="mt-2">
                    <div className="text-[10px] uppercase tracking-wider text-[hsl(var(--destructive))] font-mono mb-1">Secret findings</div>
                    <pre className="text-[10px] font-mono p-2 bg-[hsl(var(--code-bg))] border border-border rounded whitespace-pre-wrap">{JSON.stringify(manifest.secret_findings, null, 2)}</pre>
                  </div>
                )}
                {(!manifest.secret_findings || manifest.secret_findings.length === 0) && (
                  <div className="flex items-center gap-2 mt-2 text-[hsl(var(--success))] text-xs">
                    <ShieldCheck className="h-4 w-4" /> Secret scan: clean
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
