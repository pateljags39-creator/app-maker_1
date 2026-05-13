import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileArchive, Link2, Upload, Sparkles, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { Input } from '@/components/ui/input';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

const MAX_MB = 100;
const SAMPLE_URLS = [
  'https://github.com/pateljags39-creator/app-maker_1.git',
];

export default function Ingest() {
  const nav = useNavigate();
  const [mode, setMode] = useState('zip'); // 'zip' | 'url'
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState('');
  const [createdId, setCreatedId] = useState(null);
  const [poll, setPoll] = useState(null);
  const pollTimer = useRef(null);

  // Poll ingest status until terminal.
  useEffect(() => {
    if (!createdId) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const s = await api.getIngestStatus(createdId);
        if (cancelled) return;
        setPoll(s);
        if (s.ingest_status === 'complete' || s.ingest_status === 'complete_with_warning' || s.ingest_status === 'failed') {
          if (pollTimer.current) clearInterval(pollTimer.current);
          if (s.ingest_status === 'failed') toast.error(`Ingest failed: ${s.ingest_error || 'unknown'}`);
          else toast.success('Ingest complete — redirecting to Cockpit…');
          setTimeout(() => nav(`/projects/${createdId}/cockpit`), 1200);
        }
      } catch (e) {
        if (cancelled) return;
        console.warn('poll failed', e);
      }
    };
    tick();
    pollTimer.current = setInterval(tick, 2500);
    return () => {
      cancelled = true;
      if (pollTimer.current) clearInterval(pollTimer.current);
    };
    // eslint-disable-next-line
  }, [createdId]);

  const onPickFile = (f) => {
    if (!f) { setFile(null); return; }
    if (!f.name.toLowerCase().endsWith('.zip')) {
      toast.error('Only .zip files are accepted');
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      toast.error(`File too large: max ${MAX_MB} MB`);
      return;
    }
    setFile(f);
    if (!name) setName(f.name.replace(/\.zip$/i, '').slice(0, 120));
  };

  const submit = async (e) => {
    e?.preventDefault?.();
    setSubmitting(true);
    setProgress('');
    try {
      let rec;
      if (mode === 'zip') {
        if (!file) { toast.error('Choose a .zip file first'); setSubmitting(false); return; }
        setProgress('Uploading & extracting…');
        rec = await api.ingestZip(file, name.trim());
      } else {
        if (!url.trim()) { toast.error('Paste a public https:// git URL'); setSubmitting(false); return; }
        setProgress('Cloning repository…');
        rec = await api.ingestUrl(url.trim(), name.trim());
      }
      toast.success(`Project '${rec.name}' created · BRD inference running…`);
      setCreatedId(rec.id);
      setProgress('Inferring BRD from code (1 Pro call)…');
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || 'Ingest failed';
      toast.error(msg);
      setProgress('');
    } finally {
      setSubmitting(false);
    }
  };

  // While polling, show progress card.
  if (createdId) {
    const done = poll?.ingest_status === 'complete' || poll?.ingest_status === 'complete_with_warning';
    const failed = poll?.ingest_status === 'failed';
    return (
      <div className="max-w-2xl mx-auto flex flex-col gap-4">
        <div className="surface-1 p-6 flex items-start gap-4">
          <div className={"flex h-10 w-10 items-center justify-center rounded-md border shrink-0 " + (failed ? 'bg-red-500/15 border-red-500/40' : done ? 'bg-emerald-500/15 border-emerald-500/40' : 'bg-[hsl(var(--primary)/0.18)] border-[hsl(var(--primary)/0.35)]')}>
            {failed ? <AlertTriangle className="h-5 w-5 text-red-400" />
              : done ? <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              : <Sparkles className="h-5 w-5 text-[hsl(var(--primary))] animate-pulse" />}
          </div>
          <div className="flex-1">
            <div className="text-lg font-semibold">{failed ? 'Ingest failed' : done ? 'Ingest complete' : 'Ingesting…'}</div>
            <div className="text-xs text-muted-foreground mt-1 font-mono">project #{createdId}</div>
            <div className="text-xs text-muted-foreground mt-1">{poll?.ingest_source}</div>
            <div className="text-xs mt-3">
              Status: <code className="font-mono text-foreground">{poll?.ingest_status || progress || 'starting'}</code>
            </div>
            {failed && poll?.ingest_error && (
              <div className="mt-3 text-xs text-red-400 font-mono whitespace-pre-wrap">{poll.ingest_error}</div>
            )}
            {done && (
              <div className="mt-3 text-xs text-muted-foreground">Redirecting to project Cockpit…</div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-4">
      <div className="surface-1 p-6">
        <div className="flex items-center gap-2 mb-2">
          <Upload className="h-4 w-4 text-[hsl(var(--primary))]" />
          <div className="text-sm font-semibold">Import existing project</div>
        </div>
        <p className="text-xs text-muted-foreground mb-4">
          Drop a ZIP or paste a public git URL. We extract safely, infer a BRD from the code,
          detect the architecture, and unlock <strong>Improve / Fix</strong> on the result.
          One <code>gemini-2.5-pro</code> call is used for BRD inference (everything else is deterministic).
        </p>

        <div className="flex gap-1 mb-4 surface-2 p-1 rounded-md w-fit">
          <button
            onClick={() => setMode('zip')}
            className={`px-3 py-1.5 text-xs rounded ${mode === 'zip' ? 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]' : 'text-muted-foreground hover:text-foreground'}`}
            data-testid="ingest-tab-zip"
          >
            <FileArchive className="h-3.5 w-3.5 inline mr-1" /> ZIP upload
          </button>
          <button
            onClick={() => setMode('url')}
            className={`px-3 py-1.5 text-xs rounded ${mode === 'url' ? 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]' : 'text-muted-foreground hover:text-foreground'}`}
            data-testid="ingest-tab-url"
          >
            <Link2 className="h-3.5 w-3.5 inline mr-1" /> Git URL
          </button>
        </div>

        <form onSubmit={submit} className="flex flex-col gap-4">
          {mode === 'zip' ? (
            <label className="flex flex-col gap-2 cursor-pointer">
              <span className="text-xs font-medium text-muted-foreground">ZIP file (max {MAX_MB} MB)</span>
              <input
                type="file"
                accept=".zip,application/zip"
                onChange={(e) => onPickFile(e.target.files?.[0])}
                className="text-xs file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-xs file:bg-[hsl(var(--primary))] file:text-[hsl(var(--primary-foreground))] hover:file:bg-[hsl(var(--primary)/0.9)] file:cursor-pointer"
                data-testid="ingest-zip-file-input"
              />
              {file && (
                <span className="text-[11px] text-muted-foreground font-mono">{file.name} · {(file.size / 1024).toFixed(0)} KB</span>
              )}
            </label>
          ) : (
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-medium text-muted-foreground">Public git URL (https://)</span>
              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/owner/repo.git"
                data-testid="ingest-url-input"
              />
              <div className="flex flex-wrap gap-1 mt-1">
                {SAMPLE_URLS.map(s => (
                  <button type="button" key={s} onClick={() => setUrl(s)} className="text-[10px] font-mono text-[hsl(var(--link))] underline">
                    use sample
                  </button>
                ))}
              </div>
            </label>
          )}

          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-muted-foreground">Project name (optional — inferred if blank)</span>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., My Imported Notes"
              maxLength={120}
              data-testid="ingest-name-input"
            />
          </label>

          <div className="flex items-center gap-2 mt-1">
            <button
              type="submit"
              disabled={submitting || (mode === 'zip' ? !file : !url.trim())}
              data-testid="ingest-submit-button"
              className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-4 py-2 text-sm font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50"
            >
              <Upload className="h-4 w-4" />
              {submitting ? (progress || 'Working…') : (mode === 'zip' ? 'Upload & ingest' : 'Clone & ingest')}
            </button>
            <StatusBadge status="REAL" label="Sandboxed extraction" />
          </div>
        </form>
      </div>

      <div className="surface-2 p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 shrink-0" />
          <div className="text-[11px] text-muted-foreground leading-relaxed">
            <strong className="text-foreground">Safety</strong> · ZIPs are checked for zip-slip, symlinks,
            and over-budget files. Git URLs must be <code>https://</code> (private/local IPs refused),
            cloned <code>--depth=1</code> with a {MAX_MB} MB ceiling. Heavy dirs (<code>node_modules</code>,
            <code>.git</code>, <code>dist</code>, <code>build</code>, <code>__pycache__</code>) are stripped
            before any AI sees the code.
          </div>
        </div>
      </div>
    </div>
  );
}
