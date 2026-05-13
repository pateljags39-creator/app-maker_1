import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { File, Folder, Copy } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import api from '@/lib/api';

export default function FilesPage() {
  const { project } = useOutletContext();
  const [list, setList] = useState([]);
  const [selected, setSelected] = useState(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    api.listFiles(project.id).then(r => {
      if (!alive) return;
      const files = (r.files || []).filter(f => f.kind === 'file');
      setList(files);
      if (files.length && !selected) setSelected(files[0].path);
    }).catch(() => {});
    return () => { alive = false; };
    // eslint-disable-next-line
  }, [project.id]);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    api.fileContent(project.id, selected).then(t => setContent(t)).catch(() => setContent('')).finally(() => setLoading(false));
  }, [project.id, selected]);

  const copy = () => {
    navigator.clipboard.writeText(content || '').then(() => toast.success('Copied to clipboard'));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4 min-h-[60vh]">
      <div className="surface-1 overflow-hidden" data-testid="file-tree">
        <div className="border-b border-border px-3 py-2 text-[10px] uppercase tracking-wider text-muted-foreground font-mono flex items-center justify-between">
          <span>Files ({list.length})</span>
        </div>
        <ScrollArea className="h-[60vh]">
          <div className="flex flex-col gap-0.5 p-2">
            {list.length === 0 && <div className="text-xs text-muted-foreground italic p-2">No files yet — run generation first.</div>}
            {list.map(f => (
              <button
                key={f.path}
                onClick={() => setSelected(f.path)}
                data-testid="file-tree-item"
                className={`flex items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs font-mono ${selected === f.path ? 'bg-[hsl(var(--primary)/0.12)] border border-[hsl(var(--primary)/0.30)]' : 'hover:bg-accent border border-transparent'}`}
              >
                <File className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                <span className="truncate">{f.path}</span>
              </button>
            ))}
          </div>
        </ScrollArea>
      </div>
      <div className="surface-1 overflow-hidden flex flex-col" data-testid="code-viewer">
        <div className="border-b border-border px-3 py-2 flex items-center justify-between gap-2">
          <div className="text-xs font-mono truncate">{selected || '— select a file —'}</div>
          {selected && (
            <button onClick={copy} data-testid="copy-code-button" className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground">
              <Copy className="h-3.5 w-3.5" /> Copy
            </button>
          )}
        </div>
        <div className="flex-1 overflow-auto bg-[hsl(var(--code-bg))]">
          {loading ? (
            <div className="p-4 text-xs text-muted-foreground italic">Loading…</div>
          ) : selected ? (
            <pre className="p-4 text-xs leading-6 font-mono whitespace-pre-wrap break-all text-foreground">{content}</pre>
          ) : (
            <div className="p-4 text-xs text-muted-foreground italic">Select a file from the tree.</div>
          )}
        </div>
      </div>
    </div>
  );
}
