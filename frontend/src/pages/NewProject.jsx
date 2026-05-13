import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Lightbulb } from 'lucide-react';
import { toast } from 'sonner';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

const EXAMPLES = [
  'A personal notes app: create, list, view, delete. Offline-first on my laptop. No login.',
  'A team todo app: tasks with title/status/due date; tasks grouped by project; track completion rate.',
  'A contact book: people with name/email/phone/notes; search; tags; CSV export.',
];

export default function NewProject() {
  const nav = useNavigate();
  const [name, setName] = useState('');
  const [idea, setIdea] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim() || idea.trim().length < 5) return;
    setSubmitting(true);
    setError(null);
    try {
      const p = await api.createProject({ name: name.trim(), idea: idea.trim() });
      toast.success(`Project '${p.name}' created`);
      nav(`/projects/${p.id}/brd`);
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to create project';
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-4">
      <div className="surface-1 p-6">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="h-4 w-4 text-[hsl(var(--primary))]" />
          <div className="text-sm font-semibold">New Project</div>
        </div>
        <p className="text-xs text-muted-foreground mb-4">
          Give it a short name and describe the app idea. The next step is an SME-style BRD
          interview where the system asks targeted questions to make your spec generation-ready.
        </p>
        <form onSubmit={submit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-muted-foreground">Project name</span>
            <Input
              data-testid="new-project-name-input"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g., Personal Notes"
              maxLength={120}
              required
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-muted-foreground">Product idea (1–3 sentences)</span>
            <Textarea
              data-testid="new-project-idea-textarea"
              value={idea}
              onChange={e => setIdea(e.target.value)}
              placeholder="Describe what you want to build, who uses it, and any constraints (offline? auth? integrations?)."
              rows={5}
              minLength={5}
              required
              className="font-sans"
            />
            <span className="text-[10px] text-muted-foreground">{idea.length} chars</span>
          </label>
          {error && (
            <div data-testid="error-alert" className="text-xs text-[hsl(var(--destructive))] font-mono">{String(error)}</div>
          )}
          <div className="flex items-center gap-2 mt-1">
            <button
              data-testid="create-project-submit-button"
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-4 py-2 text-sm font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50"
            >
              {submitting ? 'Creating…' : 'Create & start BRD'}
            </button>
            <StatusBadge status="REAL" label="Real workspace created" />
          </div>
        </form>
      </div>

      <div className="surface-2 p-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
          <Lightbulb className="h-3.5 w-3.5" /> <span>Examples (click to prefill)</span>
        </div>
        <div className="flex flex-col gap-2">
          {EXAMPLES.map((ex, i) => (
            <button
              key={i}
              onClick={() => setIdea(ex)}
              className="text-left text-xs font-mono text-muted-foreground hover:text-foreground border border-border rounded-md px-3 py-2 hover:bg-[hsl(var(--surface-3))]"
            >{ex}</button>
          ))}
        </div>
      </div>
    </div>
  );
}
