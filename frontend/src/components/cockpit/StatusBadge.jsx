import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Ban, CircleDashed } from 'lucide-react';

const CONFIG = {
  PASS:        { label: 'Pass',        cls: 'bg-[hsl(var(--success)/0.14)] text-[hsl(var(--success))] border-[hsl(var(--success)/0.35)]',     Icon: CheckCircle2 },
  REAL:        { label: 'Real',        cls: 'bg-[hsl(var(--success)/0.14)] text-[hsl(var(--success))] border-[hsl(var(--success)/0.35)]',     Icon: CheckCircle2 },
  PARTIAL:     { label: 'Partial',     cls: 'bg-[hsl(var(--warning)/0.14)] text-[hsl(var(--warning))] border-[hsl(var(--warning)/0.35)]',     Icon: AlertTriangle },
  WARN:        { label: 'Warning',     cls: 'bg-[hsl(var(--warning)/0.14)] text-[hsl(var(--warning))] border-[hsl(var(--warning)/0.35)]',     Icon: AlertTriangle },
  FAIL:        { label: 'Fail',        cls: 'bg-[hsl(var(--destructive)/0.14)] text-[hsl(var(--destructive))] border-[hsl(var(--destructive)/0.35)]', Icon: XCircle },
  UNSUPPORTED: { label: 'Unsupported', cls: 'bg-[hsl(var(--destructive)/0.14)] text-[hsl(var(--destructive))] border-[hsl(var(--destructive)/0.35)]', Icon: XCircle },
  BLOCKED:     { label: 'Blocked',     cls: 'bg-[hsl(var(--blocked)/0.14)] text-[hsl(var(--blocked))] border-[hsl(var(--blocked)/0.35)]',     Icon: Ban },
  PLACEHOLDER: { label: 'Placeholder', cls: 'bg-transparent text-muted-foreground border border-dashed border-border', Icon: CircleDashed },
  IDLE:        { label: 'Idle',        cls: 'bg-muted text-muted-foreground border-border', Icon: CircleDashed },
};

export function StatusBadge({ status, label, className = '', testid }) {
  const key = String(status || 'IDLE').toUpperCase();
  const cfg = CONFIG[key] || CONFIG.IDLE;
  const { Icon } = cfg;
  return (
    <span
      data-testid={testid || `status-badge-${key.toLowerCase()}`}
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${cfg.cls} ${className}`}
      aria-label={`Status: ${cfg.label}`}
    >
      <Icon className="h-3 w-3" />
      <span>{label || cfg.label}</span>
    </span>
  );
}

export default StatusBadge;
