import React, { useEffect, useState } from 'react';
import { Zap, ZapOff, CircleAlert } from 'lucide-react';
import api from '@/lib/api';

export function SystemHealthPill({ className = '' }) {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancel = false;
    const load = async () => {
      try {
        const h = await api.health();
        if (!cancel) { setHealth(h); setError(null); }
      } catch (e) {
        if (!cancel) setError(e);
      }
    };
    load();
    const id = setInterval(load, 15000);
    return () => { cancel = true; clearInterval(id); };
  }, []);

  if (error) {
    return (
      <span
        data-testid="system-health-pill"
        className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium bg-[hsl(var(--destructive)/0.12)] text-[hsl(var(--destructive))] border-[hsl(var(--destructive)/0.35)] ${className}`}
      >
        <CircleAlert className="h-3.5 w-3.5" />
        <span>API offline</span>
      </span>
    );
  }
  if (!health) {
    return (
      <span data-testid="system-health-pill" className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium bg-muted text-muted-foreground border-border ${className}`}>
        <span className="h-2 w-2 rounded-full bg-muted-foreground" />
        Connecting…
      </span>
    );
  }
  const primary = health.primary_available;
  const fallback = health.fallback_available;
  let label = 'LLM: Primary Gemini';
  let cls = 'bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))] border-[hsl(var(--success)/0.35)]';
  let Icon = Zap;
  if (!primary && fallback) {
    label = 'LLM: Fallback (quota)';
    cls = 'bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))] border-[hsl(var(--warning)/0.35)]';
    Icon = ZapOff;
  } else if (!primary && !fallback) {
    label = 'LLM offline';
    cls = 'bg-[hsl(var(--destructive)/0.12)] text-[hsl(var(--destructive))] border-[hsl(var(--destructive)/0.35)]';
    Icon = CircleAlert;
  }
  return (
    <span
      data-testid="system-health-pill"
      title={`Model ${health.model}`}
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${cls} ${className}`}
    >
      <Icon className="h-3.5 w-3.5" />
      <span>{label}</span>
      <span className="font-mono text-[10px] opacity-70">{health.model}</span>
    </span>
  );
}

export default SystemHealthPill;
