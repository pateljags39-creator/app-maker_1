import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, Circle, Filter, Pause, Play, Trash2, X } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';
import useEventStream from '@/lib/useEventStream';

const SEV_CONF = {
  info:    { dot: 'bg-[hsl(var(--info))]', label: 'info' },
  success: { dot: 'bg-[hsl(var(--success))]', label: 'ok' },
  warning: { dot: 'bg-[hsl(var(--warning))]', label: 'warn' },
  error:   { dot: 'bg-[hsl(var(--destructive))]', label: 'err' },
};

function Row({ evt }) {
  const [open, setOpen] = useState(false);
  const sev = SEV_CONF[evt.severity || 'info'] || SEV_CONF.info;
  const ts = new Date((evt.created_at || 0) * 1000);
  return (
    <motion.div
      data-testid="event-ledger-row"
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="rounded-md border border-border bg-card hover:bg-accent/30 transition-colors duration-150"
    >
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-start gap-2 px-3 py-2 text-left"
      >
        <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${sev.dot}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-[11px] font-mono text-muted-foreground">
            <span>{ts.toLocaleTimeString()}</span>
            <span className="truncate">{evt.actor || 'system'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium truncate">{evt.type}</span>
          </div>
          {evt.message && (
            <div className="text-xs text-muted-foreground truncate">{evt.message}</div>
          )}
        </div>
        <div className="shrink-0 self-center text-muted-foreground">
          {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </div>
      </button>
      <AnimatePresence initial={false}>
        {open && evt.payload && Object.keys(evt.payload).length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden border-t border-border bg-[hsl(var(--code-bg))]"
          >
            <pre className="px-3 py-2 text-[11px] font-mono whitespace-pre-wrap break-all text-muted-foreground">
{JSON.stringify(evt.payload, null, 2)}
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function EventLedgerDrawer({ projectId }) {
  const [historical, setHistorical] = useState([]);
  const [paused, setPaused] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    let alive = true;
    if (!projectId) return undefined;
    api.listEvents(projectId, 50).then(list => {
      if (alive) setHistorical(Array.isArray(list) ? list : []);
    }).catch(() => {});
    return () => { alive = false; };
  }, [projectId]);

  const url = projectId && !paused ? api.eventsStreamUrl(projectId) : null;
  const { events: live, status, clear } = useEventStream(url, { enabled: !!url });

  const merged = [...live, ...historical.filter(h => !live.find(l => l.id === h.id))]
    .filter(e => filter === 'all' || (e.severity || 'info') === filter)
    .slice(0, 200);

  const conn = paused ? 'paused' : status;

  return (
    <div data-testid="event-ledger-drawer" className="h-full flex flex-col">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <div className="font-semibold">Event Ledger</div>
        <div
          data-testid="event-ledger-connection-status"
          className="ml-2 inline-flex items-center gap-1 text-[11px] font-mono text-muted-foreground"
        >
          <Circle className={`h-2 w-2 ${
            conn === 'open' ? 'fill-[hsl(var(--success))] text-[hsl(var(--success))]'
            : conn === 'paused' ? 'fill-[hsl(var(--warning))] text-[hsl(var(--warning))]'
            : conn === 'error' ? 'fill-[hsl(var(--destructive))] text-[hsl(var(--destructive))]'
            : 'fill-muted-foreground text-muted-foreground'
          }`} />
          {conn}
        </div>
        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={() => setPaused(p => !p)}
            className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs hover:bg-accent"
            data-testid="event-ledger-pause-button"
          >
            {paused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
            {paused ? 'Resume' : 'Pause'}
          </button>
          <button
            onClick={clear}
            className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs hover:bg-accent"
            data-testid="event-ledger-clear-button"
          >
            <Trash2 className="h-3 w-3" /> Clear live
          </button>
        </div>
      </div>
      <div className="flex items-center gap-1 px-3 py-2 border-b border-border">
        <Filter className="h-3.5 w-3.5 text-muted-foreground" />
        {['all', 'info', 'success', 'warning', 'error'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`text-xs rounded-md px-2 py-1 border ${filter === f ? 'border-[hsl(var(--primary)/0.45)] bg-[hsl(var(--primary)/0.10)] text-foreground' : 'border-transparent text-muted-foreground hover:bg-accent'}`}
          >{f}</button>
        ))}
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-2 p-3">
          {merged.length === 0 && (
            <div className="text-xs text-muted-foreground italic px-2 py-6 text-center">No events yet.</div>
          )}
          {merged.map((e, i) => (
            <Row key={(e.id || '') + i} evt={e} />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

export default EventLedgerDrawer;
