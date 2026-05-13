import React from 'react';

const MAP = {
  Idea:         { dot: 'bg-muted-foreground', cls: 'bg-muted text-foreground border-border' },
  BRD:          { dot: 'bg-[hsl(var(--info))]', cls: 'bg-[hsl(var(--info)/0.12)] text-[hsl(var(--info))] border-[hsl(var(--info)/0.35)]' },
  Architecture: { dot: 'bg-[hsl(var(--primary))]', cls: 'bg-[hsl(var(--primary)/0.12)] text-[hsl(var(--primary))] border-[hsl(var(--primary)/0.35)]' },
  Plan:         { dot: 'bg-muted-foreground', cls: 'bg-[hsl(var(--primary)/0.10)] text-foreground border-border' },
  Generating:   { dot: 'bg-[hsl(var(--primary))]', cls: 'bg-[hsl(var(--primary)/0.14)] text-[hsl(var(--primary))] border-[hsl(var(--primary)/0.35)]' },
  Building:     { dot: 'bg-[hsl(var(--warning))]', cls: 'bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))] border-[hsl(var(--warning)/0.35)]' },
  Repair:       { dot: 'bg-[hsl(var(--blocked))]', cls: 'bg-[hsl(var(--blocked)/0.12)] text-[hsl(var(--blocked))] border-[hsl(var(--blocked)/0.35)]' },
  Acceptance:   { dot: 'bg-[hsl(var(--success))]', cls: 'bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))] border-[hsl(var(--success)/0.35)]' },
  Export:       { dot: 'bg-muted-foreground', cls: 'bg-secondary text-secondary-foreground border-border' },
};

export function StatePill({ state, className = '' }) {
  const cfg = MAP[state] || MAP.Idea;
  return (
    <span
      data-testid="project-state-pill"
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${cfg.cls} ${className}`}
    >
      <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
      <span>{state || 'Idea'}</span>
    </span>
  );
}

export default StatePill;
