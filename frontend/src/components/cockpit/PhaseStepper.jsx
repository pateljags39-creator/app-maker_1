import React from 'react';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

const STATES = ['Idea', 'BRD', 'Architecture', 'Plan', 'Generating', 'Building', 'Repair', 'Acceptance', 'Export'];

export function PhaseStepper({ currentState }) {
  const idx = Math.max(0, STATES.indexOf(currentState));
  return (
    <div data-testid="project-phase-stepper" className="surface-1 p-4 overflow-x-auto">
      <div className="flex items-center gap-2 min-w-max">
        {STATES.map((s, i) => {
          const status = i < idx ? 'done' : i === idx ? 'current' : 'future';
          return (
            <React.Fragment key={s}>
              <div
                className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium ${
                  status === 'done' ? 'bg-[hsl(var(--success)/0.10)] text-[hsl(var(--success))] border-[hsl(var(--success)/0.35)]'
                  : status === 'current' ? 'bg-[hsl(var(--primary)/0.14)] text-[hsl(var(--primary))] border-[hsl(var(--primary)/0.35)]'
                  : 'bg-card text-muted-foreground border-border'
                }`}
              >
                {status === 'done' ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : status === 'current' ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Circle className="h-3.5 w-3.5" />
                )}
                <span>{s}</span>
              </div>
              {i < STATES.length - 1 && (
                <div className={`h-px w-6 ${i < idx ? 'bg-[hsl(var(--success))]' : 'bg-border'}`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

export default PhaseStepper;
