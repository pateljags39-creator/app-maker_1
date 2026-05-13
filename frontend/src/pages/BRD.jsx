import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { toast } from 'sonner';
import { MessageSquareQuote, Wand2, RefreshCw } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import StatusBadge from '@/components/cockpit/StatusBadge';
import api from '@/lib/api';

const CAT_COLORS = {
  data: 'border-[hsl(var(--info)/0.4)] text-[hsl(var(--info))]',
  users: 'border-[hsl(var(--success)/0.4)] text-[hsl(var(--success))]',
  workflows: 'border-[hsl(var(--warning)/0.4)] text-[hsl(var(--warning))]',
  integrations: 'border-[hsl(var(--blocked)/0.4)] text-[hsl(var(--blocked))]',
  ui: 'border-[hsl(var(--primary)/0.4)] text-[hsl(var(--primary))]',
  non_functional: 'border-muted-foreground/40 text-muted-foreground',
  constraints: 'border-[hsl(var(--destructive)/0.4)] text-[hsl(var(--destructive))]',
};

function mapStatus(status) {
  switch ((status || '').toLowerCase()) {
    case 'supported': return 'REAL';
    case 'partial': return 'PARTIAL';
    case 'unsupported': return 'UNSUPPORTED';
    case 'blocked': return 'BLOCKED';
    default: return 'PLACEHOLDER';
  }
}

export default function BRDPage() {
  const { project, refresh } = useOutletContext();
  const [brdDoc, setBrdDoc] = useState(null);
  const [loadingQ, setLoadingQ] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [answers, setAnswers] = useState({}); // qid -> { question, answer }

  const load = async () => {
    const doc = await api.getBrd(project.id);
    setBrdDoc(doc);
    // hydrate answers from existing
    const map = {};
    (doc.answers || []).forEach(a => { map[a.question_id] = { question: a.question, answer: a.answer }; });
    setAnswers(map);
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [project.id]);

  const askQuestions = async () => {
    try {
      setLoadingQ(true);
      await api.generateQuestions(project.id);
      toast.success('SME questions generated');
      await load();
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to generate questions');
    } finally { setLoadingQ(false); }
  };

  const submit = async () => {
    const list = (brdDoc?.questions || [])
      .map(q => ({ question_id: q.id || q.text?.slice(0, 16) || 'q', question: q.text || '', answer: (answers[q.id]?.answer || '').trim() }))
      .filter(a => a.answer.length > 0);
    if (list.length === 0) {
      toast.message('Answer at least one question first.');
      return;
    }
    try {
      setSubmitting(true);
      await api.submitAnswers(project.id, list);
      toast.success('BRD updated');
      await load();
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed');
    } finally { setSubmitting(false); }
  };

  const questions = brdDoc?.questions || [];
  const brd = brdDoc?.brd || {};
  const maturity = brdDoc?.maturity || 0;
  const requirements = brd.requirements || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 flex flex-col gap-4">
        <div className="surface-1 p-5">
          <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
            <div className="flex items-center gap-2">
              <MessageSquareQuote className="h-4 w-4 text-[hsl(var(--info))]" />
              <div className="text-sm font-semibold">SME interview</div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={askQuestions}
                disabled={loadingQ}
                data-testid="brd-generate-questions-button"
                className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-3 py-1.5 text-xs font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50"
              >
                {loadingQ ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Wand2 className="h-3.5 w-3.5" />}
                {questions.length ? 'Regenerate questions' : 'Generate questions'}
              </button>
            </div>
          </div>

          {questions.length === 0 && (
            <div className="text-xs text-muted-foreground italic">Click “Generate questions” to start the BRD interview.</div>
          )}
          <div className="flex flex-col gap-3">
            {questions.map((q, i) => {
              const id = q.id || String(i);
              const cls = CAT_COLORS[q.category] || 'border-border text-muted-foreground';
              return (
                <div data-testid="brd-question-card" key={id} className="rounded-lg border border-border p-4 bg-card">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <Badge variant="outline" className={`text-[10px] font-mono uppercase ${cls}`}>{q.category || 'general'}</Badge>
                      <span className="text-[10px] font-mono text-muted-foreground">#{id}</span>
                    </div>
                  </div>
                  <div className="text-sm font-medium leading-snug mb-3">{q.text}</div>
                  {q.why_it_matters && (
                    <div className="text-[11px] text-muted-foreground italic mb-3">Why this matters: {q.why_it_matters}</div>
                  )}
                  <Textarea
                    data-testid={`brd-answer-textarea-${id}`}
                    rows={3}
                    value={answers[id]?.answer || ''}
                    onChange={e => setAnswers(prev => ({ ...prev, [id]: { question: q.text, answer: e.target.value } }))}
                    placeholder="Your answer…"
                    className="font-sans"
                  />
                </div>
              );
            })}
          </div>
          {questions.length > 0 && (
            <div className="mt-4 flex items-center gap-2">
              <button
                data-testid="brd-submit-answers-button"
                onClick={submit}
                disabled={submitting}
                className="inline-flex items-center gap-2 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-4 py-2 text-sm font-medium hover:bg-[hsl(var(--primary)/0.9)] disabled:opacity-50"
              >
                {submitting ? 'Saving…' : 'Save answers & derive BRD'}
              </button>
              <span className="text-[11px] text-muted-foreground font-mono">BRD is derived by the LLM from your answers.</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <div className="surface-1 p-5" data-testid="brd-maturity-gauge">
          <div className="text-sm font-semibold mb-1">BRD maturity</div>
          <div className="text-[11px] text-muted-foreground font-mono mb-3">how generation-ready the spec is</div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-semibold font-mono">{maturity}</span>
            <span className="text-xs text-muted-foreground">/ 100</span>
          </div>
          <Progress value={maturity} className="mt-3" />
          {brd?.maturity?.missing?.length > 0 && (
            <div className="mt-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono mb-1">Missing</div>
              <ul className="text-xs space-y-1">
                {brd.maturity.missing.slice(0, 6).map((m, i) => (
                  <li key={i} className="text-muted-foreground">• {m}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        <div className="surface-1 p-5">
          <div className="text-sm font-semibold mb-2">Requirements</div>
          <div className="flex flex-col gap-2 max-h-[420px] overflow-auto">
            {requirements.length === 0 && (
              <div className="text-xs text-muted-foreground italic">No requirements yet — answer questions first.</div>
            )}
            {requirements.map((r, i) => (
              <div key={r.id || i} data-testid="brd-requirement-row" className="flex items-start justify-between gap-2 rounded-md border border-border p-2.5">
                <div className="min-w-0">
                  <div className="text-xs font-medium truncate">{r.text || r.id}</div>
                  {r.reason && <div className="text-[10px] font-mono text-muted-foreground truncate">{r.reason}</div>}
                </div>
                <StatusBadge status={mapStatus(r.status)} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
